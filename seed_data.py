"""
Optional: Populate the database with sample data for testing.
Usage: python seed_data.py
"""
import os, django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User
from items.models import LostItem, FoundItem

# Create test users
def get_or_create_user(username, first_name, last_name, role='student'):
    u, created = User.objects.get_or_create(username=username, defaults={
        'first_name': first_name, 'last_name': last_name,
        'email': f'{username}@campus.edu', 'role': role
    })
    if created:
        u.set_password('test1234')
        u.save()
    return u

u1 = get_or_create_user('alice', 'Alice', 'Wanjiku')
u2 = get_or_create_user('bob', 'Bob', 'Ochieng')
u3 = get_or_create_user('carol', 'Carol', 'Akinyi')

today = date.today()

# Lost items
lost_samples = [
    ('Black Samsung Galaxy S21', 'electronics', 'library', 'Left it on a desk near the magazine section, black case with a small crack.', today - timedelta(days=2)),
    ('Blue Graphic Novel Backpack', 'bags', 'cafeteria', 'Navy blue bag with laptop compartment. Has my name tag inside.', today - timedelta(days=1)),
    ('University ID Card', 'documents', 'lecture_hall', 'ID card for Alice Wanjiku, Eng Dept.', today),
]
for title, cat, loc, desc, d in lost_samples:
    LostItem.objects.get_or_create(title=title, defaults={
        'reporter': u1, 'category': cat, 'location_lost': loc,
        'description': desc, 'date_lost': d,
        'contact_email': u1.email, 'status': 'active'
    })

# Found items
found_samples = [
    ('Samsung Android Phone', 'electronics', 'library', 'Black Samsung phone, cracked case, found on a table near the reference section.', today - timedelta(days=1)),
    ('Blue Canvas Backpack', 'bags', 'cafeteria', 'Navy blue backpack found under a cafeteria chair.', today),
]
for title, cat, loc, desc, d in found_samples:
    FoundItem.objects.get_or_create(title=title, defaults={
        'finder': u2, 'category': cat, 'location_found': loc,
        'description': desc, 'date_found': d,
        'contact_email': u2.email, 'current_holding': 'Security Office', 'status': 'available'
    })

print("Sample data created successfully!")
print("Users: alice/test1234, bob/test1234, carol/test1234")
