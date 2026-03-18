# Installing Without Internet Access

If your machine cannot reach PyPI (pip install fails with network errors),
follow one of these approaches:

---

## Option A — Install on a machine WITH internet, copy to target

On an internet-connected machine (same OS):
```bash
pip download Django Pillow -d ./pip_packages/
```
Copy the `pip_packages/` folder to your target machine, then:
```bash
pip install --no-index --find-links=./pip_packages Django Pillow
```

---

## Option B — Django may already be installed

Check first:
```bash
python -c "import django; print(django.__version__)"
```
If this prints a version number (any version 4.2 or higher), Django is already available.
Then just skip `pip install` and run:
```bash
python manage.py migrate --run-syncdb
python manage.py shell -c "
from accounts.models import User
User.objects.create_superuser('admin','admin@campus.edu','admin123',
    first_name='Campus', last_name='Admin', role='admin')
"
python manage.py runserver
```

---

## Option C — Use a virtual environment with pre-installed packages

```bash
# If virtualenv is available:
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Then install from offline packages:
pip install --no-index --find-links=./pip_packages Django Pillow
python manage.py migrate --run-syncdb
python manage.py runserver
```

---

## Supported Django Versions

This project works with **Django 4.2, 5.x, and 6.x** (tested on 6.0.3).
The `requirements.txt` has no upper version cap intentionally.
