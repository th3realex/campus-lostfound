from django.db import models
from django.conf import settings

CATEGORY_CHOICES = [
    ('electronics', 'Electronics'),
    ('clothing', 'Clothing & Accessories'),
    ('books', 'Books & Stationery'),
    ('documents', 'Documents & IDs'),
    ('keys', 'Keys'),
    ('bags', 'Bags & Backpacks'),
    ('jewelry', 'Jewelry & Watches'),
    ('sports', 'Sports Equipment'),
    ('money', 'Money & Cards'),
    ('other', 'Other'),
]

LOCATION_CHOICES = [
    ('library', 'Library'),
    ('cafeteria', 'Cafeteria'),
    ('lecture_hall', 'Lecture Hall'),
    ('hostel', 'Hostel / Dormitory'),
    ('sports_ground', 'Sports Ground'),
    ('parking', 'Parking Area'),
    ('admin_block', 'Administration Block'),
    ('lab', 'Laboratory'),
    ('chapel', 'Chapel / Mosque'),
    ('clinic', 'Health Clinic'),
    ('other', 'Other'),
]


class LostItem(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('matched', 'Matched'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lost_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location_lost = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    location_detail = models.CharField(max_length=200, blank=True)
    date_lost = models.DateField()
    image = models.ImageField(upload_to='lost_items/', blank=True, null=True)
    proof_of_ownership = models.ImageField(upload_to='ownership_proof/', blank=True, null=True,
        help_text='Upload a previous photo, receipt, or any proof this item belongs to you')
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    reward = models.CharField(max_length=100, blank=True)

    # Verification answers — only true owner knows these
    verif_color = models.CharField(max_length=100, blank=True,
        verbose_name='Item colour / appearance',
        help_text='Describe the exact colour, brand markings, or appearance')
    verif_distinguishing = models.CharField(max_length=200, blank=True,
        verbose_name='Distinguishing feature',
        help_text='Any scratches, stickers, engravings, or unique marks?')
    verif_secret = models.CharField(max_length=200, blank=True,
        verbose_name='Secret detail',
        help_text='Something only you would know (e.g. lock screen wallpaper, bag contents, note inside)')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Lost: {self.title} by {self.reporter}"


class FoundItem(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('matched', 'Matched'),
        ('returned', 'Returned'),
        ('unclaimed', 'Unclaimed - Donated'),
    ]
    finder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='found_items')
    title = models.CharField(max_length=200)

    # Public description — vague, no identifying details
    public_description = models.TextField(
        verbose_name='Public Description (vague)',
        help_text='Describe the item vaguely — DO NOT include serial numbers, passwords, or secret details. E.g. "A black electronic device"')

    # Private description — full details, only shown to admin and verified owner
    private_description = models.TextField(
        verbose_name='Private Description (confidential)',
        help_text='Full details: exact colour, markings, serial number, contents — only admin and verified owner will see this')

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location_found = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    location_detail = models.CharField(max_length=200, blank=True,
        help_text='Exact spot — this is kept private and not shown publicly')
    date_found = models.DateField()
    image = models.ImageField(upload_to='found_items/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    current_holding = models.CharField(max_length=200, blank=True,
        help_text='Where is the item currently kept? (private)')

    # Finder's verification answers (what they observed)
    verif_color = models.CharField(max_length=100, blank=True,
        verbose_name='Colour / appearance observed',
        help_text='Exact colour, brand, or appearance as you found it')
    verif_distinguishing = models.CharField(max_length=200, blank=True,
        verbose_name='Distinguishing features observed',
        help_text='Any scratches, stickers, engravings, or unique marks you noticed')
    verif_secret = models.CharField(max_length=200, blank=True,
        verbose_name='Additional private detail',
        help_text='Any other detail not visible from outside (e.g. item inside a bag, note tucked in)')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Found: {self.title} by {self.finder}"


class ItemMatch(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    # Fraud flag choices
    FRAUD_RISK_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk — Review Carefully'),
    ]

    lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, related_name='matches')
    found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='matches')
    matched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='matches_made')
    match_score = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Fraud detection fields
    fraud_risk = models.CharField(max_length=10, choices=FRAUD_RISK_CHOICES, default='low')
    fraud_flags = models.TextField(blank=True,
        help_text='Auto-detected fraud warning flags')
    reporter_viewed_found_before_reporting = models.BooleanField(default=False,
        help_text='True if reporter viewed this found item BEFORE submitting their lost report')
    verif_color_match = models.BooleanField(null=True, blank=True,
        verbose_name='Colour answers match?')
    verif_distinguishing_match = models.BooleanField(null=True, blank=True,
        verbose_name='Distinguishing feature answers match?')
    verif_secret_match = models.BooleanField(null=True, blank=True,
        verbose_name='Secret detail answers match?')
    admin_verif_notes = models.TextField(blank=True,
        verbose_name='Admin verification notes')

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='reviewed_matches')
    owner_notified = models.BooleanField(default=False)
    finder_notified = models.BooleanField(default=False)
    owner_confirmed = models.BooleanField(null=True, blank=True)
    finder_confirmed = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ['lost_item', 'found_item']
        ordering = ['-created_at']

    def __str__(self):
        return f"Match: {self.lost_item} <-> {self.found_item} [{self.status}]"

    @property
    def verification_score(self):
        """How many of the 3 verification checks passed."""
        checks = [self.verif_color_match, self.verif_distinguishing_match, self.verif_secret_match]
        passed = sum(1 for c in checks if c is True)
        total = sum(1 for c in checks if c is not None)
        return f"{passed}/{total}" if total > 0 else "Not reviewed"

    @property
    def both_confirmed(self):
        return self.owner_confirmed and self.finder_confirmed


class FoundItemView(models.Model):
    """Tracks when a user views a found item — used for fraud detection."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='found_item_views')
    found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user} viewed {self.found_item} at {self.viewed_at}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('match_found', 'Potential Match Found'),
        ('match_approved', 'Match Approved'),
        ('match_rejected', 'Match Rejected'),
        ('item_returned', 'Item Returned'),
        ('new_lost', 'New Lost Item Posted'),
        ('new_found', 'New Found Item Posted'),
        ('fraud_alert', 'Fraud Alert'),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_match = models.ForeignKey(ItemMatch, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notif to {self.recipient}: {self.title}"
