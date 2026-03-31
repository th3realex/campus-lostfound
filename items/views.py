from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from functools import wraps

from .models import LostItem, FoundItem, ItemMatch, Notification, FoundItemView
from .forms import LostItemForm, FoundItemForm, MatchVerificationForm, ItemSearchForm
from .utils import (find_potential_matches, create_match, notify_match_parties,
                    notify_match_approved, notify_match_rejected, notify_fraud_alert)


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin_user:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def home(request):
    recent_lost = LostItem.objects.filter(status='active')[:6]
    recent_found = FoundItem.objects.filter(status='available')[:6]
    stats = {
        'total_lost': LostItem.objects.count(),
        'total_found': FoundItem.objects.count(),
        'total_resolved': ItemMatch.objects.filter(status='completed').count(),
        'pending_matches': ItemMatch.objects.filter(status='pending').count(),
    }
    return render(request, 'items/home.html', {
        'recent_lost': recent_lost,
        'recent_found': recent_found,
        'stats': stats,
    })


@login_required
def report_lost(request):
    if request.method == 'POST':
        form = LostItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.reporter = request.user
            item.contact_email = item.contact_email or request.user.email
            item.save()
            potential = find_potential_matches(item, 'lost')
            auto_approved = 0
            escalated = 0
            for found_item, score in potential[:3]:
                match, created = create_match(item, found_item, request.user, score)
                if created:
                    if match.status == 'approved':
                        auto_approved += 1
                    else:
                        escalated += 1
                        if match.fraud_risk == 'high':
                            from accounts.models import User
                            admins = User.objects.filter(Q(role='admin') | Q(is_staff=True))
                            notify_fraud_alert(match, admins)

            if auto_approved:
                messages.success(request, f'Lost item reported! A match was found and automatically verified — check your notifications for contact details.')
            elif escalated:
                messages.success(request, f'Lost item reported! A potential match was found and is under review — you will be notified shortly.')
            else:
                messages.success(request, 'Lost item reported! We will notify you when a match is found.')
            return redirect('lost_item_detail', pk=item.pk)
    else:
        form = LostItemForm()
    return render(request, 'items/report_lost.html', {'form': form})


@login_required
def report_found(request):
    if request.method == 'POST':
        form = FoundItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.finder = request.user
            item.contact_email = item.contact_email or request.user.email
            item.save()
            potential = find_potential_matches(item, 'found')
            auto_approved = 0
            escalated = 0
            for lost_item, score in potential[:3]:
                match, created = create_match(lost_item, item, request.user, score)
                if created:
                    if match.status == 'approved':
                        auto_approved += 1
                    else:
                        escalated += 1
                        if match.fraud_risk == 'high':
                            from accounts.models import User
                            admins = User.objects.filter(Q(role='admin') | Q(is_staff=True))
                            notify_fraud_alert(match, admins)

            if auto_approved:
                messages.success(request, 'Found item reported! A match was automatically verified — the owner has been notified.')
            elif escalated:
                messages.success(request, 'Found item reported! A potential match is under review — both parties will be notified shortly.')
            else:
                messages.success(request, 'Found item reported! Thank you for your honesty. We will notify you when a match is found.')
            return redirect('found_item_detail', pk=item.pk)
    else:
        form = FoundItemForm()
    return render(request, 'items/report_found.html', {'form': form})


def lost_items_list(request):
    form = ItemSearchForm(request.GET)
    items = LostItem.objects.filter(status='active')
    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        location = form.cleaned_data.get('location')
        if q:
            items = items.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if category:
            items = items.filter(category=category)
        if location:
            items = items.filter(location_lost=location)
    return render(request, 'items/lost_list.html', {'items': items, 'form': form})


def found_items_list(request):
    form = ItemSearchForm(request.GET)
    items = FoundItem.objects.filter(status='available')
    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        location = form.cleaned_data.get('location')
        if q:
            items = items.filter(Q(title__icontains=q) | Q(public_description__icontains=q))
        if category:
            items = items.filter(category=category)
        if location:
            items = items.filter(location_found=location)
    return render(request, 'items/found_list.html', {'items': items, 'form': form})


def lost_item_detail(request, pk):
    item = get_object_or_404(LostItem, pk=pk)
    return render(request, 'items/lost_detail.html', {'item': item})


def found_item_detail(request, pk):
    item = get_object_or_404(FoundItem, pk=pk)
    # Track who views found items and when — for fraud detection
    if request.user.is_authenticated and not request.user.is_admin_user:
        FoundItemView.objects.get_or_create(user=request.user, found_item=item,
            defaults={'viewed_at': timezone.now()})
    # Only show private details to admin or verified match owner
    show_private = request.user.is_authenticated and (
        request.user.is_admin_user or
        item.finder == request.user or
        ItemMatch.objects.filter(
            found_item=item,
            lost_item__reporter=request.user,
            status='approved'
        ).exists()
    )
    return render(request, 'items/found_detail.html', {'item': item, 'show_private': show_private})


@login_required
def my_items(request):
    my_lost = LostItem.objects.filter(reporter=request.user)
    my_found = FoundItem.objects.filter(finder=request.user)
    return render(request, 'items/my_items.html', {'my_lost': my_lost, 'my_found': my_found})


@login_required
def notifications(request):
    notifs = Notification.objects.filter(recipient=request.user)
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'items/notifications.html', {'notifications': notifs})


@login_required
def unread_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


# ── ADMIN VIEWS ────────────────────────────────────────────────────────────────

@login_required
@admin_required
def admin_dashboard(request):
    pending_matches = ItemMatch.objects.filter(status='pending')
    high_risk = ItemMatch.objects.filter(status='pending', fraud_risk='high')
    approved_matches = ItemMatch.objects.filter(status='approved')
    auto_approved = ItemMatch.objects.filter(status='approved', reviewed_by=None)
    all_lost = LostItem.objects.all()
    all_found = FoundItem.objects.all()
    return render(request, 'items/admin_dashboard.html', {
        'pending_matches': pending_matches,
        'high_risk': high_risk,
        'approved_matches': approved_matches,
        'auto_approved': auto_approved,
        'all_lost': all_lost,
        'all_found': all_found,
    })


@login_required
@admin_required
def admin_matches(request):
    matches = ItemMatch.objects.all().select_related(
        'lost_item', 'found_item', 'lost_item__reporter', 'found_item__finder')
    status_filter = request.GET.get('status', '')
    risk_filter = request.GET.get('risk', '')
    if status_filter:
        matches = matches.filter(status=status_filter)
    if risk_filter:
        matches = matches.filter(fraud_risk=risk_filter)
    return render(request, 'items/admin_matches.html', {
        'matches': matches, 'status_filter': status_filter, 'risk_filter': risk_filter})


@login_required
@admin_required
def match_detail(request, pk):
    match = get_object_or_404(ItemMatch, pk=pk)
    form = MatchVerificationForm(instance=match)
    return render(request, 'items/match_detail.html', {'match': match, 'form': form})


@login_required
@admin_required
def approve_match(request, pk):
    match = get_object_or_404(ItemMatch, pk=pk)
    if request.method == 'POST':
        form = MatchVerificationForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
        match.status = 'approved'
        match.reviewed_at = timezone.now()
        match.reviewed_by = request.user
        match.save()
        match.lost_item.status = 'matched'
        match.lost_item.save()
        match.found_item.status = 'matched'
        match.found_item.save()
        notify_match_approved(match)
        messages.success(request, 'Match approved — both parties notified with contact details.')
    return redirect('admin_matches')


@login_required
@admin_required
def reject_match(request, pk):
    match = get_object_or_404(ItemMatch, pk=pk)
    if request.method == 'POST':
        form = MatchVerificationForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
        match.status = 'rejected'
        match.reviewed_at = timezone.now()
        match.reviewed_by = request.user
        match.save()
        notify_match_rejected(match)
        messages.warning(request, 'Match rejected — both parties notified.')
    return redirect('admin_matches')


@login_required
@admin_required
def complete_match(request, pk):
    match = get_object_or_404(ItemMatch, pk=pk)
    match.status = 'completed'
    match.save()
    match.lost_item.status = 'resolved'
    match.lost_item.save()
    match.found_item.status = 'returned'
    match.found_item.save()
    messages.success(request, 'Match completed — item successfully returned!')
    return redirect('admin_matches')


@login_required
@admin_required
def create_manual_match(request):
    lost_items = LostItem.objects.filter(status='active')
    found_items = FoundItem.objects.filter(status='available')
    if request.method == 'POST':
        lost_id = request.POST.get('lost_item')
        found_id = request.POST.get('found_item')
        notes = request.POST.get('notes', '')
        lost_item = get_object_or_404(LostItem, pk=lost_id)
        found_item = get_object_or_404(FoundItem, pk=found_id)
        from .utils import calculate_match_score
        score = calculate_match_score(lost_item, found_item)
        match, created = create_match(lost_item, found_item, request.user, score, notes)
        if created:
            notify_match_parties(match)
            messages.success(request, f'Manual match created (score: {score}%). Both parties notified.')
        else:
            messages.info(request, 'A match between these items already exists.')
        return redirect('admin_matches')
    return render(request, 'items/create_manual_match.html', {
        'lost_items': lost_items, 'found_items': found_items})
