from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Notification


def calculate_match_score(lost_item, found_item):
    score = 0
    if lost_item.category == found_item.category:
        score += 40
    if lost_item.location_lost == found_item.location_found:
        score += 20
    lost_words = set((lost_item.title + ' ' + lost_item.description).lower().split())
    found_words = set((found_item.title + ' ' + found_item.public_description + ' ' + found_item.private_description).lower().split())
    stop_words = {'the', 'a', 'an', 'is', 'it', 'in', 'on', 'at', 'and', 'or', 'was', 'i', 'my'}
    lost_words -= stop_words
    found_words -= stop_words
    if lost_words and found_words:
        common = lost_words & found_words
        overlap = len(common) / max(len(lost_words), len(found_words))
        score += int(overlap * 30)
    if lost_item.date_lost and found_item.date_found:
        delta = abs((found_item.date_found - lost_item.date_lost).days)
        if delta == 0: score += 10
        elif delta <= 1: score += 8
        elif delta <= 3: score += 5
        elif delta <= 7: score += 2
    return min(score, 100)


def detect_fraud_flags(lost_item, found_item, reporter_viewed_before):
    """
    Analyse a match for fraud indicators.
    Returns (risk_level, flags_list).
    """
    flags = []
    risk = 'low'

    # Flag 1: Reporter viewed the found item before filing the lost report
    if reporter_viewed_before:
        flags.append('⚠️ Reporter viewed this found item BEFORE submitting their lost report')
        risk = 'high'

    # Flag 2: Lost report was filed AFTER the found item was posted
    if lost_item.created_at > found_item.created_at:
        flags.append('⚠️ Lost item report was submitted AFTER the found item was posted')
        if risk != 'high':
            risk = 'medium'

    # Flag 3: Suspiciously similar wording (possible copy-paste)
    lost_desc = lost_item.description.lower()
    found_pub = found_item.public_description.lower()
    lost_words = set(lost_desc.split())
    found_words = set(found_pub.split())
    stop_words = {'the', 'a', 'an', 'is', 'it', 'in', 'on', 'at', 'and', 'or', 'was', 'i', 'my', 'was', 'item'}
    lost_words -= stop_words
    found_words -= stop_words
    if lost_words and found_words:
        overlap = len(lost_words & found_words) / max(len(lost_words), len(found_words))
        if overlap > 0.7:
            flags.append(f'⚠️ Description overlap is very high ({int(overlap*100)}%) — possible copy from public listing')
            if risk != 'high':
                risk = 'medium'

    # Flag 4: Reporter has no previous activity (new account, first report)
    reporter = lost_item.reporter
    total_reports = reporter.lost_items.count()
    if total_reports == 1:
        flags.append('ℹ️ This is the reporter\'s first and only lost item report')

    # Flag 5: No proof of ownership uploaded
    if not lost_item.proof_of_ownership:
        flags.append('ℹ️ No proof of ownership was uploaded by the reporter')

    # Flag 6: No verification answers provided
    if not lost_item.verif_color and not lost_item.verif_distinguishing and not lost_item.verif_secret:
        flags.append('⚠️ Reporter provided NO verification answers — cannot confirm ownership')
        if risk == 'low':
            risk = 'medium'

    return risk, flags


def find_potential_matches(item, item_type='lost'):
    from .models import LostItem, FoundItem, ItemMatch
    matches = []
    THRESHOLD = 40
    if item_type == 'lost':
        candidates = FoundItem.objects.filter(status='available', category=item.category)
        for candidate in candidates:
            if not ItemMatch.objects.filter(lost_item=item, found_item=candidate).exists():
                score = calculate_match_score(item, candidate)
                if score >= THRESHOLD:
                    matches.append((candidate, score))
    else:
        candidates = LostItem.objects.filter(status='active', category=item.category)
        for candidate in candidates:
            if not ItemMatch.objects.filter(lost_item=candidate, found_item=item).exists():
                score = calculate_match_score(candidate, item)
                if score >= THRESHOLD:
                    matches.append((candidate, score))
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def compare_verification_answers(lost_item, found_item):
    """
    Compare the verification answers between the lost item reporter
    and the found item finder. Returns a dict with results and a
    confidence score 0-100.
    """
    results = {
        'color': None,
        'distinguishing': None,
        'secret': None,
        'confidence': 0,
        'answered_count': 0,
        'matched_count': 0,
    }

    def similarity(a, b):
        """Check if two answers are meaningfully similar."""
        if not a or not b:
            return None
        a = a.lower().strip()
        b = b.lower().strip()
        # Exact or near-exact match
        if a == b:
            return True
        # Word overlap — if more than 50% of words match it counts
        a_words = set(a.split())
        b_words = set(b.split())
        if not a_words or not b_words:
            return None
        overlap = len(a_words & b_words) / max(len(a_words), len(b_words))
        return overlap >= 0.5

    checks = [
        ('color', lost_item.verif_color, found_item.verif_color),
        ('distinguishing', lost_item.verif_distinguishing, found_item.verif_distinguishing),
        ('secret', lost_item.verif_secret, found_item.verif_secret),
    ]

    answered = 0
    matched = 0

    for key, lost_ans, found_ans in checks:
        result = similarity(lost_ans, found_ans)
        results[key] = result
        if result is not None:
            answered += 1
            if result:
                matched += 1

    results['answered_count'] = answered
    results['matched_count'] = matched

    # Confidence score based on how many checks passed
    if answered == 0:
        results['confidence'] = 0
    else:
        results['confidence'] = int((matched / answered) * 100)

    return results


def auto_verify_match(match):
    """
    Core auto-verification engine.

    Decision logic:
    - LOW fraud risk + HIGH verification confidence (>=67%) → AUTO-APPROVE
    - HIGH fraud risk (any) → ESCALATE to admin, never auto-approve
    - MEDIUM fraud risk → ESCALATE to admin
    - LOW fraud risk + LOW confidence → ESCALATE to admin
    - No verification answers provided at all → ESCALATE to admin

    Returns: 'approved' | 'escalated'
    """
    from django.utils import timezone
    from accounts.models import User
    from django.db.models import Q

    lost_item = match.lost_item
    found_item = match.found_item

    # Step 1 — Run verification answer comparison
    verif = compare_verification_answers(lost_item, found_item)

    # Store results on the match
    match.verif_color_match = verif['color']
    match.verif_distinguishing_match = verif['distinguishing']
    match.verif_secret_match = verif['secret']

    # Step 2 — Decision tree
    fraud_risk = match.fraud_risk
    confidence = verif['confidence']
    answered = verif['answered_count']

    auto_approved = False
    reason = ''

    if fraud_risk == 'high':
        reason = '🚨 High fraud risk detected — requires manual admin review'

    elif fraud_risk == 'medium':
        reason = '⚠️ Medium fraud risk detected — requires manual admin review'

    elif answered == 0:
        reason = '⚠️ No verification answers provided by either party — requires manual review'

    elif confidence >= 67:
        # All clear — auto approve
        auto_approved = True
        reason = f'✅ Auto-approved: {verif["matched_count"]}/{answered} verification checks passed ({confidence}% confidence), fraud risk is low'

    else:
        reason = f'⚠️ Verification confidence too low ({confidence}%) — {verif["matched_count"]}/{answered} checks passed — requires manual review'

    # Step 3 — Apply decision
    match.admin_verif_notes = reason

    if auto_approved:
        match.status = 'approved'
        match.reviewed_at = timezone.now()
        match.reviewed_by = None  # system-approved
        match.save()

        # Update item statuses
        lost_item.status = 'matched'
        lost_item.save()
        found_item.status = 'matched'
        found_item.save()

        # Notify both parties with full contact details
        notify_match_approved(match)
        return 'approved'

    else:
        # Escalate to admin
        match.save()
        admins = User.objects.filter(Q(role='admin') | Q(is_staff=True))
        notify_fraud_alert(match, admins)
        # Still notify both parties that a match is under review
        notify_match_parties(match)
        return 'escalated'


def create_match(lost_item, found_item, matched_by, score=0, notes=''):
    from .models import ItemMatch, FoundItemView

    # Check if reporter viewed this found item before reporting
    viewed_before = False
    if lost_item.created_at:
        viewed_before = FoundItemView.objects.filter(
            user=lost_item.reporter,
            found_item=found_item,
            viewed_at__lt=lost_item.created_at
        ).exists()

    risk, flags = detect_fraud_flags(lost_item, found_item, viewed_before)

    match, created = ItemMatch.objects.get_or_create(
        lost_item=lost_item,
        found_item=found_item,
        defaults={
            'matched_by': matched_by,
            'match_score': score,
            'notes': notes,
            'fraud_risk': risk,
            'fraud_flags': '\n'.join(flags),
            'reporter_viewed_found_before_reporting': viewed_before,
        }
    )

    # Run auto-verification immediately after creating the match
    if created:
        auto_verify_match(match)

    return match, created


def send_notification(recipient, notif_type, title, message, match=None):
    Notification.objects.create(
        recipient=recipient,
        notification_type=notif_type,
        title=title,
        message=message,
        related_match=match,
    )
    if recipient.email:
        try:
            send_mail(
                subject=f'[Campus Lost & Found] {title}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=True,
            )
        except Exception:
            pass


def notify_match_parties(match):
    lost_item = match.lost_item
    found_item = match.found_item
    owner_msg = (
        f"A potential match has been found for your lost item '{lost_item.title}'.\n\n"
        f"An item in the '{found_item.get_category_display()}' category was found "
        f"near {found_item.get_location_found_display()} around {found_item.date_found}.\n\n"
        f"An admin will review this match and verify your ownership details before approving.\n"
        f"You will be notified once the review is complete."
    )
    send_notification(lost_item.reporter, 'match_found',
        f"Potential match found for '{lost_item.title}'", owner_msg, match)
    match.owner_notified = True

    finder_msg = (
        f"A potential owner has been identified for the item you found: '{found_item.title}'.\n\n"
        f"An admin will verify their ownership before sharing any contact details.\n"
        f"You will be notified of the outcome."
    )
    send_notification(found_item.finder, 'match_found',
        f"Potential owner found for '{found_item.title}'", finder_msg, match)
    match.finder_notified = True
    match.save()


def notify_match_approved(match):
    lost_item = match.lost_item
    found_item = match.found_item
    owner_msg = (
        f"Your ownership of '{lost_item.title}' has been VERIFIED and the match APPROVED.\n\n"
        f"Finder details:\n"
        f"Name: {found_item.finder.get_full_name()}\n"
        f"Email: {found_item.contact_email or found_item.finder.email}\n"
        f"Phone: {found_item.contact_phone or found_item.finder.phone or 'N/A'}\n"
        f"Item is currently at: {found_item.current_holding or found_item.get_location_found_display()}\n\n"
        f"Please contact the finder to arrange collection."
    )
    send_notification(lost_item.reporter, 'match_approved', 'Ownership Verified — Match Approved!', owner_msg, match)

    finder_msg = (
        f"The owner of '{found_item.title}' has been verified.\n\n"
        f"Owner details:\n"
        f"Name: {lost_item.reporter.get_full_name()}\n"
        f"Email: {lost_item.contact_email or lost_item.reporter.email}\n"
        f"Phone: {lost_item.contact_phone or lost_item.reporter.phone or 'N/A'}\n\n"
        f"They will contact you to arrange collection."
    )
    send_notification(found_item.finder, 'match_approved', 'Owner Verified — Match Approved!', finder_msg, match)


def notify_match_rejected(match):
    send_notification(
        match.lost_item.reporter, 'match_rejected',
        f"Match not confirmed for '{match.lost_item.title}'",
        f"The proposed match for your lost item was reviewed and not confirmed.\n"
        f"We will continue looking for a match.", match)
    send_notification(
        match.found_item.finder, 'match_rejected',
        f"Match not confirmed for '{match.found_item.title}'",
        f"The proposed match for the item you found was not confirmed.\n"
        f"The item remains available for its rightful owner to claim.", match)


def notify_fraud_alert(match, admin_users):
    """Alert all admins about a high-risk match."""
    for admin in admin_users:
        send_notification(
            admin, 'fraud_alert',
            f"🚨 High Fraud Risk Match #{match.pk}",
            f"A high-risk match has been flagged:\n\n{match.fraud_flags}\n\n"
            f"Lost item: {match.lost_item.title} (by {match.lost_item.reporter.get_full_name()})\n"
            f"Found item: {match.found_item.title}\n\nPlease review carefully.",
            match
        )
