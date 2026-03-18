"""
Run this to create the default admin account.
Usage: python create_admin.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User

if not User.objects.filter(username='admin').exists():
    u = User.objects.create_superuser(
        username='admin',
        email='admin@campus.edu',
        password='admin123',
        first_name='Campus',
        last_name='Admin',
        role='admin'
    )
    print(f"Superuser created: {u.username} | password: admin123")
else:
    print("Admin account already exists.")
