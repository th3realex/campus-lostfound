@echo off
echo.
echo ==============================================
echo      Campus Lost & Found - Django App
echo ==============================================
echo.

python --version >nul 2>&1 || (
    echo ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)

python -c "import django" >nul 2>&1 || (
    echo [1/4] Installing Django...
    pip install Django Pillow
)

echo [2/4] Setting up database...
python manage.py migrate --run-syncdb

echo [3/4] Creating admin account...
python manage.py shell -c "from accounts.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser(username='admin', email='admin@campus.edu', password='admin123', first_name='Campus', last_name='Admin', role='admin') and print('Admin created')"

mkdir media\lost_items 2>nul
mkdir media\found_items 2>nul
mkdir media\profiles 2>nul

echo.
echo ==============================================
echo   App is ready!
echo.
echo   Open browser:  http://127.0.0.1:8000
echo   Admin panel:   http://127.0.0.1:8000/admin-panel/
echo   Login:         admin / admin123
echo ==============================================
echo.

python manage.py runserver
pause
