# 🎓 Campus Lost & Found System

A full-featured Django web application for managing lost and found items on a college/university campus.

---

## ✨ Features

- **Student/Staff Registration & Login** — Role-based accounts (Student, Staff, Admin)
- **Report Lost Items** — With category, location, date, image upload, reward info
- **Report Found Items** — With holding location, finder contact, images
- **Smart Auto-Matching** — Automatically detects potential matches based on category, location, date & keywords
- **Admin Match Review** — Admins approve/reject matches through a dedicated panel
- **Notifications** — In-app + email notifications sent to both parties on match
- **Manual Match Creation** — Admins can manually link any lost + found pair
- **Item Status Tracking** — Active → Matched → Resolved / Returned
- **Search & Filter** — Filter items by keyword, category, and location

---

## 🚀 Quick Start

### Requirements
- Python 3.9 or higher
- pip

### Launch (Linux / macOS)
```bash
./start.sh
```

### Launch (Windows)
```cmd
start.bat
```

### Manual Steps (any OS)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run database migrations
python manage.py migrate

# 3. Create admin account
python create_admin.py

# 4. (Optional) Load sample test data
python seed_data.py

# 5. Start the server
python manage.py runserver
```

Then open your browser at: **http://127.0.0.1:8000**

---

## 🔐 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Test Students | `alice`, `bob`, `carol` | `test1234` (after seed_data.py) |

---

## 📁 Project Structure

```
campus_lostfound/
├── config/               # Django project settings, URLs
│   ├── settings.py
│   └── urls.py
├── accounts/             # User model, auth views, forms
│   ├── models.py         # Custom User with role, student_id, phone
│   ├── views.py
│   ├── forms.py
│   └── urls.py
├── items/                # Core app: lost, found, matches, notifications
│   ├── models.py         # LostItem, FoundItem, ItemMatch, Notification
│   ├── views.py          # All views including admin panel
│   ├── forms.py
│   ├── urls.py
│   ├── utils.py          # Matching algorithm + notification helpers
│   └── admin.py
├── templates/
│   ├── base.html
│   ├── accounts/         # login, register, profile
│   └── items/            # home, lists, details, admin, notifications
├── media/                # Uploaded item images (auto-created)
├── static/               # CSS/JS assets
├── db.sqlite3            # SQLite database (auto-created)
├── requirements.txt
├── create_admin.py       # Admin account setup
├── seed_data.py          # Sample test data
├── start.sh              # Linux/macOS launcher
└── start.bat             # Windows launcher
```

---

## ⚙️ Matching Algorithm

When a new lost or found item is reported, the system:

1. Searches all active items in the **same category**
2. Calculates a **match score (0–100)** based on:
   - Same category → **+40 pts**
   - Same location → **+20 pts**
   - Keyword overlap in title/description → **up to +30 pts**
   - Date proximity (lost vs found date) → **up to +10 pts**
3. If score ≥ 40, creates a **pending match** and notifies both parties
4. Admin reviews and **approves or rejects** the match
5. On approval, full contact details are shared with both parties

---

## 📧 Email Configuration

By default, emails print to the console (development mode). To enable real email:

Edit `config/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

---

## 🛡️ Admin Panel

Navigate to `/admin-panel/` after logging in as admin to:
- Review pending matches
- Approve / reject matches
- Manually create matches
- Mark items as returned/completed

The Django built-in admin at `/admin/` also provides full database access.

---

## 🌐 Production Notes

Before deploying to production:
1. Set `DEBUG = False` in `settings.py`
2. Change `SECRET_KEY` to a strong random value
3. Set `ALLOWED_HOSTS` to your domain
4. Use PostgreSQL instead of SQLite
5. Set up proper email (SMTP)
6. Run `python manage.py collectstatic`
