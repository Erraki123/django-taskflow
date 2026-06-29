# TaskFlow — Professional Task Management Web Application

A production-ready task management SaaS built with **Django 5**, **MySQL**, **Bootstrap 5**, and **Chart.js**. Includes authentication, a real-time AJAX-powered dashboard, full task CRUD, categories, activity logs, dark/light mode, and an automated test suite.

---

## ✨ Features

- Custom-styled login / registration / password-reset flow (login by username **or** email, "remember me")
- Auto-created user **Profile** with avatar upload, bio, job title
- Dashboard with animated stat cards, a completion-rate ring, and three Chart.js charts (status pie, priority bar, monthly line) — refreshed automatically via AJAX
- Full Task CRUD with Category tagging, priority, status, deadlines
- AJAX-powered search, filtering, sorting, pagination, status/priority quick-edit, and delete-with-confirmation — no full page reloads
- Activity log feed ("Recent activity") and upcoming-deadline notifications
- Dark / light theme toggle, persisted via cookie, no flash-of-wrong-theme
- Fully responsive (desktop / tablet / mobile) sidebar + topbar layout
- Hardened Django Admin with custom list views, filters, and search
- Per-user data isolation enforced at the queryset level (one account can never see another's tasks)
- 20 automated tests (`python manage.py test`) covering registration, login, task CRUD, permissions, and dashboard statistics

---

## 🧱 Tech stack

| Layer       | Choice                                   |
|-------------|-------------------------------------------|
| Backend     | Django 5.1 (LTS-track)                   |
| Database    | MySQL 8 (via `mysqlclient`)              |
| Frontend    | Bootstrap 5, vanilla JS (AJAX, `fetch`)  |
| Charts      | Chart.js 4                               |
| Icons       | Font Awesome 6                           |
| Auth        | Django's built-in `django.contrib.auth`  |

---

## 📁 Project structure

```
taskflow/
├── config/              # Django project settings, root urls, wsgi/asgi
├── core/                # Shared abstract models, ActivityLog, context processors
├── accounts/            # Auth, Profile model, login/register/profile views
├── tasks/               # Task & Category models, CRUD + AJAX views
├── dashboard/           # Stats aggregation + Chart.js data API
├── templates/           # Base shell, auth shell
├── static/
│   ├── css/             # tokens.css (design system) + base.css
│   └── js/              # theme.js, sidebar.js, toast.js, tasks.js, dashboard.js
├── media/               # User-uploaded avatars (created at runtime)
├── requirements.txt
├── .env.example
└── manage.py
```

---

## 🪟 Full setup on Windows (step-by-step, copy-paste in order)

These commands assume you're using **PowerShell** or **cmd.exe**, and that you've unzipped the project to a folder, e.g. `C:\Projects\taskflow`.

### 1. Prerequisites — install these first if you don't have them

- **Python 3.11+** → https://www.python.org/downloads/ (tick "Add Python to PATH" during install)
- **MySQL Server 8** (Community Server) → https://dev.mysql.com/downloads/installer/ — remember the **root password** you set during install
- **Git** (optional, only if you want version control) → https://git-scm.com/downloads

### 2. Open a terminal in the project folder

```powershell
cd C:\Projects\taskflow
```

### 3. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```
You'll know it worked when your prompt shows `(venv)` at the start.

### 4. Install all Python dependencies

```powershell
pip install -r requirements.txt
```

> **If `mysqlclient` fails to install on Windows** with a build error, install the precompiled wheel instead:
> ```powershell
> pip install mysqlclient --only-binary :all:
> ```
> If it still fails, install "Microsoft C++ Build Tools" from https://visualstudio.microsoft.com/visual-cpp-build-tools/ and retry, or fall back to `pip install pymysql` and let me know — the settings can be adapted to use PyMySQL instead.

### 5. Create the MySQL database

Open MySQL's command line (or MySQL Workbench) and run:

```sql
CREATE DATABASE taskflow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Quickest way from PowerShell, if `mysql` is on your PATH:
```powershell
mysql -u root -p -e "CREATE DATABASE taskflow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```
(It will prompt for your MySQL root password.)

### 6. Configure your environment variables

```powershell
copy .env.example .env
notepad .env
```
Edit these two lines to match your MySQL setup, then save and close Notepad:
```
DB_PASSWORD=your_actual_mysql_root_password
SECRET_KEY=replace-this-with-any-long-random-string
```

### 7. Run database migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 8. Create your admin (superuser) account

```powershell
python manage.py createsuperuser
```
Follow the prompts (username, email, password).

### 9. (Optional but recommended) Seed demo data

This creates a demo user with realistic sample tasks so the dashboard looks populated immediately:
```powershell
python manage.py seed_demo_data
```
This logs in as username `demo`, password `Demo@12345`.

### 10. Collect static files

```powershell
python manage.py collectstatic --noinput
```

### 11. Run the development server

```powershell
python manage.py runserver
```

### 12. Open the app

Go to **http://127.0.0.1:8000/accounts/login/** in your browser.

- Log in with the superuser you created in step 8, or with `demo` / `Demo@12345` if you ran the seed command.
- The Django admin is at **http://127.0.0.1:8000/admin/**.

---

### Every time you come back to work on the project later

```powershell
cd C:\Projects\taskflow
venv\Scripts\activate
python manage.py runserver
```

---

## 🐧 Setup on macOS / Linux

```bash
cd taskflow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

mysql -u root -p -e "CREATE DATABASE taskflow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

cp .env.example .env
nano .env   # set DB_PASSWORD and SECRET_KEY

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data   # optional
python manage.py collectstatic --noinput
python manage.py runserver
```

---

## ✅ Running the automated tests

```powershell
python manage.py test
```
This runs all 20 tests (registration, login, task CRUD, permission isolation, dashboard statistics) against a temporary throwaway test database — your real `taskflow_db` is never touched.

---

## 🔐 Security notes

- All task/category querysets are filtered by `user=request.user` — verified by an automated test (`test_user_cannot_access_another_users_task`).
- CSRF protection is enabled project-wide; every AJAX `POST` sends the `X-CSRFToken` header read from Django's `csrftoken` cookie.
- Password validation uses Django's built-in validators (minimum length, common-password check, similarity-to-user-info check).
- Before deploying to production, set `DEBUG=False` in `.env` and fill in `ALLOWED_HOSTS` with your real domain.

## 🚀 Going to production (brief checklist)

1. `DEBUG=False`, set a strong unique `SECRET_KEY`, and set `ALLOWED_HOSTS`.
2. Set `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True` in `.env` once you have HTTPS.
3. Serve static files with a real web server (Nginx) or a CDN, and run `collectstatic`.
4. Use a production WSGI server such as `gunicorn` (Linux) or `waitress` (Windows) instead of `manage.py runserver`.
5. Point `EMAIL_BACKEND` at a real SMTP provider so password-reset emails actually deliver.

---

## 📄 License

This project was generated as a starter/reference implementation for you to use, modify, and extend freely.
