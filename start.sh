#!/bin/bash
set -e

echo ""
echo "=============================================="
echo "     Campus Lost & Found — Django App"
echo "=============================================="
echo ""

# Check Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "ERROR: Python not found. Install Python 3.9+ from https://python.org"
    exit 1
fi

echo "[Python] Using: $($PYTHON --version)"

# Check if Django is already installed
if $PYTHON -c "import django" &>/dev/null; then
    echo "[Django] Already installed: $($PYTHON -c 'import django; print(django.__version__)')"
else
    echo "[1/4] Installing dependencies..."
    echo "      (requires internet access to PyPI)"
    pip install Django Pillow
fi

# Run migrations
echo "[2/4] Setting up database..."
$PYTHON manage.py migrate --run-syncdb

# Create admin account
echo "[3/4] Creating admin account (if not exists)..."
$PYTHON manage.py shell -c "
from accounts.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(username='admin', email='admin@campus.edu',
        password='admin123', first_name='Campus', last_name='Admin', role='admin')
    print('  Admin created: admin / admin123')
else:
    print('  Admin already exists')
"

# Create media directories
mkdir -p media/lost_items media/found_items media/profiles

echo ""
echo "=============================================="
echo "  App is ready!"
echo ""
echo "  Open browser:    http://127.0.0.1:8000"
echo "  Admin panel:     http://127.0.0.1:8000/admin-panel/"
echo "  Django admin:    http://127.0.0.1:8000/admin/"
echo ""
echo "  Login:  admin / admin123"
echo ""
echo "  Optional - load sample data:"
echo "    python seed_data.py"
echo ""
echo "  Press Ctrl+C to stop the server"
echo "=============================================="
echo ""

$PYTHON manage.py runserver
