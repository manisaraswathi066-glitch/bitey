# Bitetech Technologies — Complete Dynamic Web Application

[![Python](https://img.shields.io/badge/Python-3.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%20(WAMP)%20%7C%20SQLite-orange.svg)](https://www.mysql.com/)
[![Security](https://img.shields.io/badge/Security-OWASP%20%2B%20CSRF%20%2B%20TOTP%20MFA-purple.svg)](https://bitetechnologies.com)
[![Tests](https://img.shields.io/badge/Tests-12%20Suites%20Passing-brightgreen.svg)](https://bitetechnologies.com)

A professional, dynamic, database-driven business platform and customer portal built for **Bitetech Technologies** — specializing in Python development projects (Mini starting at ₹599, Major starting at ₹1,000), professional website development (Shop Websites starting at ₹5,000, Websites with Hosting at ₹7,000), and mentor-led online programming classes.

---

## 1. Verified Company & Commercial Information

* **Company Name:** Bitetech Technologies
* **Main Focus:** Python Development Projects, Commercial Web Development, and Online Programming Classes
* **Official Email:** `bitetechtechnologies@gmail.com`
* **Contact Phone:** `7418332912`
* **WhatsApp Direct:** `+91 7418332912`
* **Currency:** Indian Rupees (₹)
* **Pricing Structure (Strictly Verified):**
  * **Python Mini Projects:** Starting from **₹599** (Academic demos, automation scripts, console & desktop utilities)
  * **Python Major Projects:** Starting from **₹1,000** (Full-stack systems, database management, analytical platforms)
  * **Shop / Small Business Website:** Starting from **₹5,000** (Responsive catalog, WhatsApp ordering, contact forms)
  * **Website with Hosting & Domain:** Starting from **₹7,000** (Complete package: 1-year hosting, domain, deployment, SSL)
  * **Online Programming Classes:**
    * JavaScript: **₹299**
    * HTML & CSS: **₹499**
    * C Programming: **₹599**
    * C++ Programming: **₹699**
    * Python Programming: **₹899**
    * Cybersecurity Fundamentals: **₹899**
    * Data Science with Python: **₹999**
    * Artificial Intelligence Foundations: **₹999**
    * PHP & MySQL Web Development: **₹1,499**
    * Data Analysis (Pandas & Power BI): **₹1,499**

---

## 2. Key Features & Platform Capabilities

### Public Website & Catalogs
* **Modern High-Impact UI:** Curated deep navy (`#0B192C`) and indigo (`#4F46E5`) theme, Google Fonts (`Inter` & `Outfit`), glassmorphism cards, micro-animations, mobile responsive Bootstrap 5.
* **Mini Projects Catalog (`/projects/mini`):** Filtered reference projects starting at ₹599 with clear deliverables, source code tags, and direct enquiry forms.
* **Major Projects Catalog (`/projects/major`):** Advanced engineering systems starting at ₹1,000 with architectural descriptions and technology breakdowns.
* **Services & Quotes (`/services`, `/services/<slug>`):** Interactive service catalog detailing timeline, deliverables, hosting duration, domain inclusion, renewal costs, and customized quotation submission forms.
* **Online Classes Syllabus (`/courses`, `/courses/<slug>`):** Class descriptions, batch timings (weekend & weekday), learning formats, prerequisites, and registration forms.
* **Demonstration Portfolio (`/portfolio`):** Filterable portfolio of software engineering projects and reference architectures.
* **Contact Desk (`/contact`):** Subject and budget selection, anti-spam honeypot, and direct phone/WhatsApp links.
* **5 Transparent Policies:**
  1. `/privacy-policy` — Data protection, cookie usage, user privacy.
  2. `/terms` — Terms of service, engagement conditions, intellectual property.
  3. `/refund-policy` — Service cancellation and milestone refund guidelines.
  4. `/project-delivery-policy` — Delivery timelines, source code delivery, revision window.
  5. `/hosting-renewal-policy` — 1st-year hosting terms, domain renewal, third-party server costs.

### Student & Customer Account Portal
* **Registration & Auth (`/register`, `/login`, `/logout`):** Customer self-registration with Argon2/scrypt password hashing and mandatory terms acceptance.
* **Personal Dashboard (`/dashboard`):** Strict record isolation — customers view their own project requests, quotation enquiries, class enrollments, and project order statuses.
* **Profile Management (`/profile/update`):** Customers can update full name and contact phone number.
* **Self-Service Password Recovery (`/forgot-password`, `/reset-password/<token>`):** Time-limited (2-hour expiry), cryptographic token recovery flow with fallback link display for local development.

### Administrator Control Panel (`/admin`)
* **Admin Dashboard (`/admin/dashboard`):** Operational metrics, count cards, quick action links, recent inquiries preview.
* **Enquiries & Lead Management (`/admin/enquiries`):** Filter project, service, course, and contact enquiries. Update status (`New`, `Contacted`, `In Progress`, `Completed`, `Rejected`), store internal admin notes and customer responses.
* **CSV Export (`/admin/enquiries/export`):** One-click download of all enquiries formatted as CSV spreadsheet data.
* **Services Management (`/admin/services`):** Full CRUD for service packages, timelines, starting prices, hosting terms, and publication toggle.
* **Customer Management (`/admin/customers`):** Search, inspect registered customers, view linked enquiry counts, and toggle active status.
* **Project Catalog CRUD (`/admin/projects`):** Create, edit, toggle publish status, manage pricing, deliverables, and category assignment.
* **Course Catalog CRUD (`/admin/courses`):** Create, edit, syllabus builder, batch timing, pricing, and active status.
* **Categories, Portfolio & FAQs CRUD (`/admin/categories`, `/admin/portfolio`, `/admin/faqs`):** Full database-driven administration.
* **Company Settings (`/admin/settings`):** Live editing of company contact info, starting prices, hero text, and policy markdown without code changes.
* **Multi-Factor Authentication (`/admin/setup-mfa`, `/admin/verify-mfa`):** RFC 6238 TOTP authentication (Google Authenticator, Microsoft Authenticator compatible) with QR code and manual key fallback.
* **Defensive Incident Response:** Emergency lockdown switch and remote session revocation (`/admin/revoke-all-sessions`).
* **Security Audit Logs (`/admin/audit-logs`):** Immutable chronological record of logins, MFA changes, CRUD operations, and export events with IP and timestamp.

---

## 3. Technology Stack

* **Language:** Python 3.13 / 3.14
* **Web Framework:** Flask 3.1.3
* **Authentication:** Flask-Login 0.6.3
* **Database & ORM:** Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.5, Flask-Migrate 4.1.0
* **MySQL Connector:** PyMySQL 1.2.3 (Pure Python connector, zero C-compiler dependency on Windows)
* **Development Fallback:** SQLite 3 (`instance/bitetech.db`)
* **Security & Forms:** Flask-WTF 1.3.0, WTForms 3.2.2, CSRF protection, Honeypot bot protection, Security HTTP Headers
* **Frontend:** Bootstrap 5.3, Bootstrap Icons 1.11, Custom Vanilla CSS, Google Fonts

---

## 4. Quickstart Guide (Windows)

### Step 1: Open PowerShell / Command Prompt
```powershell
cd s:\bitetech\bitetech_website
```

### Step 2: Activate the Virtual Environment
The virtual environment is pre-configured in `venv`:
```powershell
# PowerShell:
.\venv\Scripts\Activate.ps1

# Command Prompt (cmd.exe):
.\venv\Scripts\activate.bat
```

*(If creating a new virtual environment from scratch)*:
```powershell
py -3.14 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 3: Initialize and Seed the Database
```powershell
.\venv\Scripts\python.exe init_db.py
```
This automatically initializes the database (SQLite by default, or WAMP MySQL if configured in `.env`), runs migrations, and seeds:
* 4 Python Mini Projects (₹599) & 4 Major Projects (₹1,000)
* 4 Web Development Services (Shop Website ₹5,000, Website with Hosting ₹7,000)
* 10 Online Programming Courses (₹299 – ₹1,499)
* 6 Project Categories, 4 Demonstration Portfolio items, 6 Categorized FAQs
* 5 Company Policies & Site Settings
* Initial Accounts:
  * **Administrator:** `admin` / `AdminSecure2026!`
  * **Customer / Student:** `student` / `StudentPass2026!`

---

## 5. Running the Application

### Option A: Standard Python Invocation
```powershell
.\venv\Scripts\python.exe app.py
```

### Option B: Flask CLI
```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_DEBUG = "True"
.\venv\Scripts\flask.exe run --host=127.0.0.1 --port=5000
```

### Access URLs:
* **Public Website:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
* **Mini Projects (₹599):** [http://127.0.0.1:5000/projects/mini](http://127.0.0.1:5000/projects/mini)
* **Major Projects (₹1,000):** [http://127.0.0.1:5000/projects/major](http://127.0.0.1:5000/projects/major)
* **Services & Quotations:** [http://127.0.0.1:5000/services](http://127.0.0.1:5000/services)
* **Online Classes:** [http://127.0.0.1:5000/courses](http://127.0.0.1:5000/courses)
* **Customer Login:** [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)
* **Customer Register:** [http://127.0.0.1:5000/register](http://127.0.0.1:5000/register)
* **Admin Login:** [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login)

---

## 6. WAMP Server MySQL Setup (Optional)

If running in a production or WAMP environment:
1. Start WAMP Server (ensure tray icon is green).
2. Open phpMyAdmin at `http://localhost/phpmyadmin`.
3. In phpMyAdmin, click **Import** and choose `s:\bitetech\bitetech_website\wamp_setup.sql`. Click **Go**.
4. Update your `.env` file:
   ```ini
   USE_SQLITE=False
   DB_USER=bitetech_app
   DB_PASSWORD=ChangeThisToAStrongAppPassword2026!
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=bitetech_db
   ```
5. Seed the MySQL database:
   ```powershell
   .\venv\Scripts\python.exe init_db.py
   ```

---

## 7. Running the Automated Test Suite

The platform includes a comprehensive, 12-suite automated test script verifying 100% of routes, security controls, form submissions, customer auth, and admin features:

```powershell
.\venv\Scripts\python.exe test_app.py
```

### What is tested:
1. Public route availability (18 endpoints including Mini ₹599, Major ₹1,000, Services, Policies)
2. Detail views for Projects, Courses, and Services
3. Form submissions & database persistence (Contact, Project Enquiry, Course Enquiry, Service Quotation)
4. Customer registration, login, profile update, and personal dashboard
5. Role isolation (Customer accounts strictly blocked from accessing `/admin`)
6. Password reset token generation, token expiry validation, and password recovery
7. Admin authentication, invalid credential lockout, and session establishment
8. Authenticated admin views (Dashboard, Enquiries, Projects, Services, Customers, Categories, Courses, Portfolio, FAQs, Settings, Audit Logs)
9. Admin Service CRUD creation
10. Admin Enquiry workflow status updates with CSRF tokens
11. CSV Export spreadsheet generation
12. Session revocation and administrator logout

---

## 8. Backup & Restore Utility

A standalone database backup and restore script is provided:

```powershell
# Create a timestamped backup (saved to backups/):
.\venv\Scripts\python.exe backup_restore.py backup

# List all available backups:
.\venv\Scripts\python.exe backup_restore.py list

# Restore from a backup:
.\venv\Scripts\python.exe backup_restore.py restore backups/backup_20261018_XXXXXX.db
```

---

## 9. Creating Additional Administrators

To create an administrator from the command line:

```powershell
# Interactive mode:
.\venv\Scripts\python.exe create_admin.py

# CLI arguments:
.\venv\Scripts\python.exe create_admin.py --username superadmin --email admin2@bitetech.in --password StrongAdminPass2026!
```

---

## 10. Security Compliance Notes

* **OWASP Top 10 Aligned:** CSRF tokens on all POST forms, SQL injection prevention via SQLAlchemy parameterized queries, XSS mitigation with Jinja2 auto-escaping, anti-spam honeypot fields on public forms.
* **Brute Force Protection:** Automatic 15-minute lockout after 5 consecutive failed login attempts.
* **Session Protection:** Session fixation defense, 30-minute inactivity timeout, token version invalidation (`/admin/revoke-all-sessions`).
* **Role-Based Access Control:** Strict boundary separation between Customers/Students (`role='customer'`) and Administrators (`role='admin'`).
* **Zero Fabricated Claims:** Strictly adheres to genuine company information (`bitetechtechnologies@gmail.com`, phone `7418332912`), authentic course pricing, and verified project starting costs.
