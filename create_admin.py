import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User
password = os.environ.get('ADMIN_PASSWORD', 'admin123')
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@campus.edu',
        password=password,
        first_name='Campus',
        last_name='Admin',
        role='admin'
    )
    print(f'Admin created with password from environment')
else:
    print('Admin already exists')