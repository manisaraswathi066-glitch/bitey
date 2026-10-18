"""
Database initialization and seeding script for Bitetech Technologies.
Creates all database tables and seeds realistic reference projects,
services with transparent hosting terms, structured online courses,
FAQs, and comprehensive site settings & policies.
"""

from app import create_app
from extensions import db
from models import (
    User, ProjectCategory, Project, Service, Course, 
    PortfolioItem, FAQ, SiteSetting, ProjectEnquiry, 
    CourseEnquiry, ServiceEnquiry, ContactMessage, ProjectOrder
)
from datetime import datetime, timezone

def init_database(seed_demo=True):
    app = create_app()
    with app.app_context():
        print("[*] Creating database tables...")
        db.create_all()
        migrate_columns()
        print("[+] Tables created and schema verified successfully.")

        if seed_demo:
            print("[*] Seeding default site settings & policies...")
            seed_settings()

            print("[*] Seeding default users (admin & student)...")
            seed_users()

            print("[*] Seeding project categories...")
            seed_categories()

            print("[*] Seeding Python projects (Mini & Major)...")
            seed_projects()

            print("[*] Seeding website & software services...")
            seed_services()

            print("[*] Seeding online programming courses...")
            seed_courses()

            print("[*] Seeding portfolio items...")
            seed_portfolio()

            print("[*] Seeding FAQs...")
            seed_faqs()

            print("[*] Seeding initial sample inquiries...")
            seed_sample_enquiries()

            db.session.commit()
            print("[OK] Database initialized and seeded successfully!")

def migrate_columns():
    """Defensive schema upgrade for SQLite & MySQL to ensure all columns and tables exist."""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()

        # If old admin_users exists, migrate to users table
        if 'admin_users' in table_names and 'users' in table_names:
            try:
                with db.engine.connect() as conn:
                    # Check if users is empty
                    user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                    if user_count == 0:
                        print("[*] Migrating records from legacy admin_users to users table...")
                        conn.execute(text("""
                            INSERT INTO users (id, username, email, password_hash, role, is_active, failed_logins, mfa_secret, mfa_enabled, token_version, created_at)
                            SELECT id, username, email, password_hash, role, is_active, failed_logins, mfa_secret, mfa_enabled, token_version, created_at
                            FROM admin_users
                        """))
                        conn.commit()
                        print("[+] Legacy admin records migrated successfully.")
            except Exception as e:
                print(f"[*] Notice on user migration: {e}")

        # Add any missing columns to projects
        if 'projects' in table_names:
            p_cols = [c['name'] for c in inspector.get_columns('projects')]
            with db.engine.connect() as conn:
                if 'project_type' not in p_cols:
                    conn.execute(text("ALTER TABLE projects ADD COLUMN project_type VARCHAR(50) DEFAULT 'Mini'"))
                if 'starting_price' not in p_cols:
                    conn.execute(text("ALTER TABLE projects ADD COLUMN starting_price INTEGER DEFAULT 599"))
                if 'problem_statement' not in p_cols:
                    conn.execute(text("ALTER TABLE projects ADD COLUMN problem_statement TEXT"))
                if 'deliverables' not in p_cols:
                    conn.execute(text("ALTER TABLE projects ADD COLUMN deliverables TEXT"))
                if 'source_code_included' not in p_cols:
                    conn.execute(text("ALTER TABLE projects ADD COLUMN source_code_included BOOLEAN DEFAULT 1"))
                if 'availability_status' not in p_cols:
                    conn.execute(text("ALTER TABLE projects ADD COLUMN availability_status VARCHAR(50) DEFAULT 'Available'"))
                conn.commit()

        # Add any missing columns to courses
        if 'courses' in table_names:
            c_cols = [c['name'] for c in inspector.get_columns('courses')]
            with db.engine.connect() as conn:
                if 'fee_integer' not in c_cols:
                    conn.execute(text("ALTER TABLE courses ADD COLUMN fee_integer INTEGER DEFAULT 899"))
                if 'delivery_mode' not in c_cols:
                    conn.execute(text("ALTER TABLE courses ADD COLUMN delivery_mode VARCHAR(50) DEFAULT 'Online Live Mentoring'"))
                if 'class_schedule' not in c_cols:
                    conn.execute(text("ALTER TABLE courses ADD COLUMN class_schedule VARCHAR(150) DEFAULT 'Weekend & Evening Batches'"))
                if 'teaching_format' not in c_cols:
                    conn.execute(text("ALTER TABLE courses ADD COLUMN teaching_format VARCHAR(150) DEFAULT 'Live Screen-Share & Code Reviews'"))
                if 'status' not in c_cols:
                    conn.execute(text("ALTER TABLE courses ADD COLUMN status VARCHAR(50) DEFAULT 'Enrolling'"))
                conn.commit()

        # Add user_id to project_enquiries
        if 'project_enquiries' in table_names:
            pe_cols = [c['name'] for c in inspector.get_columns('project_enquiries')]
            with db.engine.connect() as conn:
                if 'user_id' not in pe_cols:
                    conn.execute(text("ALTER TABLE project_enquiries ADD COLUMN user_id INTEGER"))
                if 'company_response' not in pe_cols:
                    conn.execute(text("ALTER TABLE project_enquiries ADD COLUMN company_response TEXT"))
                conn.commit()

        # Add user_id to course_enquiries
        if 'course_enquiries' in table_names:
            ce_cols = [c['name'] for c in inspector.get_columns('course_enquiries')]
            with db.engine.connect() as conn:
                if 'user_id' not in ce_cols:
                    conn.execute(text("ALTER TABLE course_enquiries ADD COLUMN user_id INTEGER"))
                if 'learning_mode' not in ce_cols:
                    conn.execute(text("ALTER TABLE course_enquiries ADD COLUMN learning_mode VARCHAR(50) DEFAULT 'Online Live'"))
                if 'company_response' not in ce_cols:
                    conn.execute(text("ALTER TABLE course_enquiries ADD COLUMN company_response TEXT"))
                conn.commit()

        # Add user_id to contact_messages
        if 'contact_messages' in table_names:
            cm_cols = [c['name'] for c in inspector.get_columns('contact_messages')]
            with db.engine.connect() as conn:
                if 'user_id' not in cm_cols:
                    conn.execute(text("ALTER TABLE contact_messages ADD COLUMN user_id INTEGER"))
                if 'company_response' not in cm_cols:
                    conn.execute(text("ALTER TABLE contact_messages ADD COLUMN company_response TEXT"))
                conn.commit()

    except Exception as e:
        print(f"[*] Schema migration notice: {e}")

def seed_users():
    # Admin User
    admin = User.query.filter((User.username == 'admin') | (User.email == 'bitetechtechnologies@gmail.com')).first()
    if not admin:
        admin = User(
            username='admin',
            email='bitetechtechnologies@gmail.com',
            full_name='System Administrator',
            phone='7418332912',
            role='admin',
            is_active=True,
            mfa_enabled=False
        )
        admin.set_password('AdminSecure2026!')
        db.session.add(admin)
        print("[+] Seeded primary admin user: 'admin'")

    # Sample Customer / Student User
    student = User.query.filter_by(username='student').first()
    if not student:
        student = User(
            username='student',
            email='student@example.com',
            full_name='Aarav Mehta',
            phone='9876543210',
            role='customer',
            is_active=True
        )
        student.set_password('StudentPass2026!')
        db.session.add(student)
        print("[+] Seeded customer user: 'student'")

    db.session.commit()

def seed_settings():
    settings = {
        'company_name': ('Bitetech Technologies', 'Official Business Name'),
        'company_email': ('bitetechtechnologies@gmail.com', 'Official Contact Email'),
        'company_phone': ('7418332912', 'Official Phone Number'),
        'whatsapp_number': ('917418332912', 'WhatsApp Direct Number with Country Code'),
        'starting_price': ('599', 'Starting price for mini projects in INR'),
        'hero_headline': ('Turning Python Ideas into Working Projects.', 'Main Hero Headline'),
        'hero_subheadline': (
            'Bitetech Technologies specializes in custom Python application development, modular database-backed systems, website development services, and mentor-led online programming classes. Get production-ready mini projects starting from just ₹599 or request full-stack websites starting from ₹5,000.',
            'Hero Supporting Text'
        ),
        'about_text': (
            'Bitetech Technologies is an independent software development and technical mentoring initiative focused on Python engineering, website development, and practical programming education. We bridge the gap between theoretical syntax and working software by building clean, maintainable applications and teaching students how to architect real projects from scratch.',
            'Company Overview'
        ),
        'mission_text': (
            'To make software engineering accessible, practical, and transparent by delivering well-structured Python projects at affordable pricing and empowering learners with real coding confidence.',
            'Mission Statement'
        ),
        'vision_text': (
            'To become a trusted technical partner for learners, creators, and small businesses seeking robust Python automation, clean web applications, and practical programming education.',
            'Vision Statement'
        ),
        'privacy_policy': (
            """## 1. Information We Collect
We collect personal information that you voluntarily provide when submitting project enquiries, requesting website development quotes, enrolling in online classes, or registering for a customer account. This includes your name, email address, phone/WhatsApp number, and project requirements.

## 2. How We Use Your Information
- To review technical requirements and provide transparent quotations.
- To schedule and conduct online programming mentoring classes.
- To communicate project milestones, deliverables, and technical updates.
- We do NOT sell, rent, or trade your personal information to third-party advertisers.

## 3. Account Data & Authentication Security
User accounts are secured with modern cryptographic password hashing (scrypt). We implement server-side role validation, CSRF verification, and rate limiting to defend against unauthorized access.

## 4. Inquiries & Data Rights
To request removal or correction of your contact details or account data, contact our data administrator at bitetechtechnologies@gmail.com.""",
            'Privacy Policy Draft'
        ),
        'terms_conditions': (
            """## 1. Scope of Services
Bitetech Technologies provides software development, Python project engineering, custom website development, and online programming education. All quotations are subject to mutual technical agreement on specifications, deliverables, and timelines.

## 2. Pricing and Payment Terms
- Python Mini Projects starting at ₹599 and Major Projects starting at ₹1,000 reflect starting baseline prices. Complex custom requirements will receive a customized quotation.
- Website development packages (Shop/Business Website starting at ₹5,000; Website with Hosting starting at ₹7,000) are starting estimates. Final quotes depend on required pages, dynamic backend logic, and chosen hosting specifications.
- Course fees are payable prior to commencement of training modules.

## 3. Intellectual Property & Code Ownership
Upon full payment, the client or student receives the agreed deliverables, including source code files for the specified project scope, subject to any open-source licenses of underlying frameworks.

## 4. Code Maintenance & Support
Every project delivery includes a complimentary 7-day technical verification period for bug fixes and local setup guidance. Extended maintenance is available under separate agreement.""",
            'Terms & Conditions Draft'
        ),
        'refund_policy': (
            """## 1. Custom Software & Digital Deliverables
Due to the digital nature of software source code and project deliverables:
- Once complete project source code or downloadable assets have been delivered, refunds cannot be issued.
- If a project cannot be delivered according to agreed technical specifications due to an issue on our end, a full or proportional refund will be issued promptly.

## 2. Online Programming Classes
- Students may request a full refund prior to the commencement of the first scheduled mentoring session.
- Once batch sessions have begun, partial refunds or batch reschedules may be granted on a case-by-case basis upon written request.

## 3. How to Request a Refund
Submit all refund requests to bitetechtechnologies@gmail.com with your Order/Enquiry ID and reason for the request. We review and respond within 3 business days.""",
            'Refund & Cancellation Policy Draft'
        ),
        'project_delivery_policy': (
            """## 1. Delivery Methods
Digital deliverables including Python source code, database setup scripts (SQLite / WAMP MySQL), and configuration files are securely delivered via electronic download link, repository transfer, or email.

## 2. Standard Delivery Timelines
- Python Mini Projects: Typically delivered within 24 to 48 hours for standard reference implementations.
- Python Major Projects & Custom Applications: Typically 5 to 10 working days, depending on scope and testing requirements.
- Website Development Packages: 5 to 7 working days for Shop/Small Business websites.

## 3. Revision Policy
- We include up to 2 rounds of minor revisions to ensure the delivered software conforms to the agreed scope.
- Substantial scope additions or modifications requested after delivery confirmation will be quoted separately.""",
            'Project Delivery & Revision Policy Draft'
        ),
        'hosting_renewal_policy': (
            """## 1. Website with Hosting Package Scope
For our ₹7,000 Website with Hosting starting package:
- Hosting duration, domain registration terms, SSL configuration, and mailbox provisions are explicitly configured and approved in the final project scope agreement.
- Standard initial packages include 1 Year of shared cloud hosting and assistance with domain registration (.com or .in) where specified.

## 2. Annual Renewal Costs
- Hosting and domain registrations must be renewed annually to keep websites live.
- Estimated renewal costs start from ₹2,500/year, billed in advance of the expiration date.
- Clients retain full rights to migrate their website source code and database to their own hosting provider at any time.""",
            'Hosting & Renewal Policy Draft'
        ),
        'incident_mode': ('normal', 'Defensive Incident Mode: normal / read_only / lockdown')
    }

    for key, (val, desc) in settings.items():
        item = SiteSetting.query.filter_by(key=key).first()
        if not item:
            item = SiteSetting(key=key, value=val, description=desc)
            db.session.add(item)
    db.session.commit()

def seed_categories():
    categories = [
        ('Python Mini Projects', 'mini-projects', 'Compact, ready-to-run Python projects starting from ₹599. Ideal for learning, rapid prototypes, and academic submissions.'),
        ('Python Major Projects', 'major-projects', 'End-to-end full-stack Python software, complete database portals, and multi-user systems starting from ₹1,000.'),
        ('Flask Web Applications', 'flask-web-apps', 'Full-stack dynamic web applications built with Flask, SQLAlchemy, MySQL, and responsive Bootstrap templates.'),
        ('Database & Inventory Systems', 'database-systems', 'Data-driven business tools, inventory managers, and CRUD applications with relational schema design.'),
        ('Automation & Scripting', 'automation-scripts', 'Python automation tools for web scraping, file processing, automated report generation, and data parsing.')
    ]
    for name, slug, desc in categories:
        if not ProjectCategory.query.filter_by(slug=slug).first():
            cat = ProjectCategory(name=name, slug=slug, description=desc)
            db.session.add(cat)
    db.session.commit()

def seed_projects():
    mini_cat = ProjectCategory.query.filter_by(slug='mini-projects').first()
    major_cat = ProjectCategory.query.filter_by(slug='major-projects').first()
    flask_cat = ProjectCategory.query.filter_by(slug='flask-web-apps').first()
    db_cat = ProjectCategory.query.filter_by(slug='database-systems').first()
    auto_cat = ProjectCategory.query.filter_by(slug='automation-scripts').first()

    projects_data = [
        # --- Python Mini Projects (Starting at ₹599) ---
        {
            'title': 'Student Attendance & Grade Tracker (Reference Demo)',
            'slug': 'student-attendance-grade-tracker',
            'category_id': mini_cat.id if mini_cat else None,
            'project_type': 'Mini',
            'starting_price': 599,
            'price_range': 'From ₹599',
            'short_description': 'A clean, modular Python application for managing student records, attendance logs, and automated grade calculation with CSV report export.',
            'problem_statement': 'Educational departments and tutors often struggle with manual attendance calculations, grade averages, and identifying students at risk of attendance shortfalls below 75%.',
            'full_description': """### Overview
The Student Attendance & Grade Tracker is a complete reference Python application designed to showcase relational data handling, CSV parsing, and automated performance calculation.

### Technical Architecture
- **Architecture**: Modular Python code divided into services, models, and CLI/GUI interfaces.
- **Relational Storage**: Stores student rosters, attendance percentages, and test scores.
- **Report Generation**: Automatically calculates GPA, identifies students with attendance below 75%, and exports printable CSV summaries.
- **Beginner Friendly**: Extensively commented source code with a comprehensive setup guide.""",
            'features': "Student profile and enrollment tracking\nAutomated attendance calculation and warnings (<75% alerts)\nGrade aggregation and GPA computing\nCSV report export and data backup\nEasy local setup with SQLite or WAMP MySQL",
            'deliverables': "Complete commented Python 3.13 source code\nSQLite & WAMP MySQL database schema scripts\nComprehensive README and execution instructions\nProject viva questions and architectural overview guide",
            'tech_stack': 'Python 3.13, SQLite / MySQL, Tabulate, CSV Module',
            'availability_status': 'Available',
            'is_demo': True,
            'is_published': True,
            'is_featured': True
        },
        {
            'title': 'Library Management & Fine Calculator (Reference Demo)',
            'slug': 'library-management-system',
            'category_id': mini_cat.id if mini_cat else None,
            'project_type': 'Mini',
            'starting_price': 599,
            'price_range': 'From ₹599',
            'short_description': 'Classic academic Python mini-project featuring book checkout, return reminders, student membership records, and automated overdue fine computation.',
            'problem_statement': 'Small libraries and academic reading rooms need an easy, automated way to track book availability, issue logs, and compute overdue fines without expensive commercial software.',
            'full_description': """### Overview
A clean, battle-tested Python project demonstrating relational data modeling between Books, Members, and Issue Logs.

### Highlights
- Calculates overdue fines automatically based on daily late fees.
- Real-time book inventory stock tracking (Available vs Issued).
- Includes step-by-step documentation and viva voce Q&A guide.""",
            'features': "Book catalog with ISBN and category tracking\nMember registration and borrowing limits\nAutomated overdue fine calculator based on days late\nSearch books by author, title, or status\nStructured database with clear foreign keys",
            'deliverables': "Full Python source code (clean PEP 8 formatted)\nDatabase tables with foreign keys (.sql and SQLite)\nSample test data for instant testing\nSetup walkthrough guide",
            'tech_stack': 'Python 3.13, SQLite / WAMP MySQL, SQL Queries',
            'availability_status': 'Available',
            'is_demo': True,
            'is_published': True,
            'is_featured': True
        },
        {
            'title': 'Automated Web Data Scraper & Excel Reporter (Demo)',
            'slug': 'web-data-scraper-reporter',
            'category_id': auto_cat.id if auto_cat else mini_cat.id,
            'project_type': 'Mini',
            'starting_price': 599,
            'price_range': 'From ₹599',
            'short_description': 'Automated Python script for parsing public web data, formatting structured datasets, and exporting styled multi-tab Excel reports.',
            'problem_statement': 'Professionals and researchers spend hours copying public table data manually into spreadsheets, leading to errors and outdated records.',
            'full_description': """### Overview
Demonstrates HTTP request orchestration, HTML DOM extraction with BeautifulSoup, respectful rate limiting, and automated multi-tab Excel spreadsheet creation.

### Ideal Use Case
Learning web scraping, automated daily reporting, competitor pricing monitoring, or academic data collection.""",
            'features': "Safe HTML parsing and data extraction\nUser-agent rotation and respectful rate limiting\nAutomatic data sanitization and type casting\nMulti-sheet Excel export with automated header formatting\nCLI interface with progress indicators",
            'deliverables': "Executable Python automation script\nRequirements.txt with verified libraries\nSample output Excel report with formatted headers\nUsage documentation",
            'tech_stack': 'Python, BeautifulSoup4, Requests, OpenPyXL, Pandas',
            'availability_status': 'Available',
            'is_demo': True,
            'is_published': True,
            'is_featured': False
        },

        # --- Python Major Projects (Starting at ₹1,000) ---
        {
            'title': 'Flask E-Billing & Invoice Generator (Major Project)',
            'slug': 'flask-billing-invoice-generator',
            'category_id': flask_cat.id if flask_cat else major_cat.id,
            'project_type': 'Major',
            'starting_price': 1000,
            'price_range': 'From ₹1,000',
            'short_description': 'A full-stack web application featuring dynamic invoice creation, itemized tax calculations, customer management, and printable receipts.',
            'problem_statement': 'Small enterprises and service freelancers require an accessible billing portal that creates professional GST/tax invoices without monthly SaaS subscription costs.',
            'full_description': """### Overview
The Flask E-Billing & Invoice Generator represents an end-to-end dynamic web application suitable for small businesses, freelancers, and engineering students learning database-driven web design.

### Technical Architecture
- **Backend**: Flask 3 with SQLAlchemy ORM.
- **Database**: Dual compatibility with MySQL (WAMP) and SQLite.
- **Frontend**: Clean Bootstrap 5 responsive UI with invoice print formatting.
- **Features**: Product catalog, customer records, multi-item tax calculations, and PDF/HTML invoice printing.""",
            'features': "Dynamic invoice generation with instant tax calculation\nCustomer registry and purchase history\nPrint-ready HTML/PDF invoice templates\nCSRF-protected forms and input sanitization\nWAMP MySQL and SQLite compatibility\nAdministrative sales metrics dashboard",
            'deliverables': "Complete Flask backend source code\nBootstrap 5 responsive frontend templates\nDatabase migration scripts for MySQL & SQLite\nPrintable invoice templates\nStep-by-step local server deployment guide",
            'tech_stack': 'Python, Flask, SQLAlchemy, MySQL, Bootstrap 5',
            'availability_status': 'Available',
            'is_demo': True,
            'is_published': True,
            'is_featured': True
        },
        {
            'title': 'Hospital & Clinic Multi-Role Appointment Portal (Major)',
            'slug': 'hospital-appointment-system',
            'category_id': db_cat.id if db_cat else major_cat.id,
            'project_type': 'Major',
            'starting_price': 1200,
            'price_range': 'From ₹1,200',
            'short_description': 'Relational database management application for doctor schedules, patient appointment booking, consultation history, and reception triage.',
            'problem_statement': 'Medical clinics often face double-booked appointment slots, lost consultation paper records, and inefficient scheduling between receptionists and doctors.',
            'full_description': """### Overview
A robust Python web application managing clinic workflows: doctor specialization registries, patient booking slots, automated schedule conflict detection, and consultation history.

### Core Architecture
- Implements role-based workflows for receptionists, doctors, and patients.
- Time-slot validation prevents double-booking.
- Includes pre-built SQL schema scripts for WAMP MySQL.""",
            'features': "Doctor scheduling and department categorization\nAppointment slot validation to prevent double booking\nPatient consultation records and history\nAdmin analytics dashboard with daily booking totals\nComplete WAMP MySQL database schema included\nPatient search and filter capabilities",
            'deliverables': "Full Flask multi-role application\nNormalized relational MySQL schema with foreign keys\nAdmin and staff authentication views\nSample patient and doctor database seed\nInstallation manual for WAMP Server",
            'tech_stack': 'Python 3, Flask, Flask-SQLAlchemy, MySQL, Jinja2',
            'availability_status': 'Available',
            'is_demo': True,
            'is_published': True,
            'is_featured': True
        },
        {
            'title': 'RESTful Authentication & Task API Service (Major)',
            'slug': 'restful-task-api-service',
            'category_id': major_cat.id if major_cat else None,
            'project_type': 'Major',
            'starting_price': 1000,
            'price_range': 'From ₹1,000',
            'short_description': 'A modular Flask REST API featuring secure token authentication, input validation, role permissions, and full CRUD endpoints.',
            'problem_statement': 'Developers building mobile apps or frontend frameworks need a secure, well-structured Python backend API with standardized error handling and token authentication.',
            'full_description': """### Overview
A clean RESTful API service showcasing modern API design in Python: JSON serialization, request validation, error handling with standard HTTP status codes, and database persistence.""",
            'features': "Token-based secure authentication\nJSON payload schema validation\nFull CRUD endpoints with standard HTTP status codes\nPagination and search parameters on list endpoints\nComprehensive API documentation and Postman collection",
            'deliverables': "Modular Flask API codebase with blueprints\nDatabase ORM models and serializers\nPostman collection for automated testing\nSetup and endpoint documentation",
            'tech_stack': 'Python, Flask, SQLAlchemy, Marshmallow, MySQL',
            'availability_status': 'Available',
            'is_demo': True,
            'is_published': True,
            'is_featured': False
        }
    ]

    for p in projects_data:
        existing = Project.query.filter_by(slug=p['slug']).first()
        if not existing:
            proj = Project(
                title=p['title'],
                slug=p['slug'],
                category_id=p['category_id'],
                project_type=p['project_type'],
                starting_price=p['starting_price'],
                price_range=p['price_range'],
                short_description=p['short_description'],
                problem_statement=p['problem_statement'],
                full_description=p['full_description'],
                features=p['features'],
                deliverables=p['deliverables'],
                tech_stack=p['tech_stack'],
                availability_status=p['availability_status'],
                is_demo=p['is_demo'],
                is_published=p['is_published'],
                is_featured=p['is_featured']
            )
            db.session.add(proj)
        else:
            # Update fields
            existing.project_type = p['project_type']
            existing.starting_price = p['starting_price']
            existing.problem_statement = p['problem_statement']
            existing.deliverables = p['deliverables']

def seed_services():
    services_data = [
        {
            'title': 'Shop or Small Business Website',
            'slug': 'shop-small-business-website',
            'starting_price': '₹5,000',
            'price_integer': 5000,
            'timeline': '5-7 Working Days',
            'short_description': 'A modern, responsive, high-converting business website designed for retail shops, local services, consultants, and startups. Showcase your products and collect customer leads directly via WhatsApp and email.',
            'full_description': """### Service Overview
Get a sleek, professional digital presence for your retail store, clinic, boutique, or local business. Our Shop and Small Business package provides a bespoke website built for speed, mobile responsiveness, and client trust.

### Note on Pricing
The starting price of **₹5,000** is an upfront baseline estimate for standard 4-5 page business showcase websites. Final quotations are transparently calculated based on the number of products, custom forms, and integrations you require.

### What is Included
- Up to 5 custom-designed responsive pages (Home, About, Services/Products, Pricing, Contact).
- Direct WhatsApp instant chat integration and lead capture form.
- Google Maps location embedding and business hours display.
- Fast-loading HTML5/CSS3/Bootstrap layout optimized for smartphones and desktops.
- Admin portal or simple instructions for updating contact details and business hours.""",
            'features': "100% Mobile, tablet, and desktop responsive design\nInstant WhatsApp inquiry button and email contact forms\nProduct / Service catalog showcase with pricing tables\nGoogle Maps location and business info integration\nBasic search engine optimization (SEO) setup\nFast loading speed with optimized images",
            'deliverables': "Complete website source code (HTML, CSS, JavaScript)\nDeployment on client hosting or local test environment\nContact form setup with email routing\nAdmin guide for updating phone numbers, addresses, and images\n14 days of post-launch technical verification",
            'project_requirements': "Business name, logo (or we provide clean typography header), contact details, list of services/products, and any brand colors.",
            'hosting_duration': 'Hosting is not included by default in this ₹5,000 package. We can deploy on your existing hosting or upgrade to our hosted package.',
            'domain_included': 'Domain registration is not included. Client provides domain or purchases separately.',
            'renewal_cost': 'No mandatory renewal fees paid to Bitetech for the code. Standard domain/hosting renewal applies to your third-party registrar.',
            'additional_charges': 'Additional pages beyond 5: ₹500/page. Payment gateway integration: ₹1,500. Custom dynamic backend portal: quoted on requirement.',
            'is_published': True,
            'is_featured': True
        },
        {
            'title': 'Website with Hosting & Domain Package',
            'slug': 'website-with-hosting',
            'starting_price': '₹7,000',
            'price_integer': 7000,
            'timeline': '7-10 Working Days',
            'short_description': 'A complete, all-inclusive online launch package. Includes custom responsive website development, initial 1-year shared cloud hosting, domain registration assistance, free SSL certificate, and business email setup.',
            'full_description': """### Service Overview
A turnkey digital solution for businesses that want everything taken care of: design, development, cloud server deployment, and domain connection without technical hassle.

### Transparent Hosting & Domain Terms
- **Starting Price**: ₹7,000 covers initial development and first-year hosting setup.
- **Hosting Duration**: 1 Year of shared cloud hosting is configured with 99.9% uptime.
- **Domain Inclusion**: Assistance with registering one .com or .in domain for the first year (subject to standard domain availability).
- **Security**: Free automated SSL/HTTPS certificate installation.
- **Business Email**: Up to 2 professional email accounts (e.g., info@yourbusiness.com).
- **Renewal Costs**: Hosting and domain must be renewed annually. Estimated renewal is ₹2,500/year after year 1. Clients may also migrate their site to any host at any time with full code portability.""",
            'features': "Complete custom website development (up to 6 responsive pages)\n1-Year Shared Cloud Hosting configured and monitored\n1st-Year Domain registration assistance (.com or .in)\nFree Let's Encrypt SSL security certificate installed\nBusiness email setup (e.g. contact@yourcompany.com)\nWeekly automated database and file backups\nMobile-friendly UI with WhatsApp and email inquiry forms",
            'deliverables': "Live hosted website accessible globally on your chosen domain\nSSL Certificate active with HTTPS enforcement\nComplete website source code and database backup provided to client\nControl panel credentials and webmail access\n30 days of complimentary maintenance and minor text revisions",
            'project_requirements': "Desired domain name, business summary, service descriptions, logo, and contact info.",
            'hosting_duration': '1 Year Shared Cloud Hosting included in base quote. Renewable annually.',
            'domain_included': 'Includes assistance with 1st-year .com or .in domain registration (standard names).',
            'renewal_cost': 'Estimated at ₹2,500 per year starting from Year 2 for continued hosting, domain renewal, and SSL maintenance.',
            'additional_charges': 'E-commerce cart functionality, payment gateways, and multi-currency support are quoted additionally based on inventory size.',
            'is_published': True,
            'is_featured': True
        },
        {
            'title': 'Custom Python Software & Automation Development',
            'slug': 'python-software-automation',
            'starting_price': '₹3,500',
            'price_integer': 3500,
            'timeline': '3-7 Working Days',
            'short_description': 'Bespoke Python automation scripts, web scrapers, data format converters, and database utilities tailored to streamline business workflows and academic research.',
            'full_description': """### Service Overview
Eliminate repetitive manual data entry, format conversion, and multi-source data collection. We build robust, error-tolerant Python automation tools that run locally or on scheduled servers.

### Common Solutions
- Scheduled public web scrapers with CSV/Excel output.
- Automated PDF invoice and receipt parsers.
- Relational database synchronization tools.
- REST API client integrations.""",
            'features': "Clean, robust Python 3.13 compatible code\nGraceful error recovery and logging\nConfigurable via environment variables or settings files\nExecutable Windows runner (.bat or GUI) for non-technical users\nCSV, Excel, JSON, and SQL database output support",
            'deliverables': "Full Python script files with detailed comments\nRequirements.txt and virtual environment guide\nWindows one-click batch launcher\nVideo/written walkthrough of script execution",
            'project_requirements': "Sample input files/data and clear explanation of target output format.",
            'hosting_duration': 'Runs on local client machine. Server cron hosting optional upon request.',
            'domain_included': 'Not applicable for desktop/CLI scripts.',
            'renewal_cost': 'None. One-time development fee.',
            'additional_charges': 'GUI interface (Tkinter/PyQt) or cloud deployment available on request.',
            'is_published': True,
            'is_featured': False
        },
        {
            'title': 'Dynamic Flask Web Application & Portal',
            'slug': 'flask-web-application-portal',
            'starting_price': '₹8,000',
            'price_integer': 8000,
            'timeline': '10-14 Working Days',
            'short_description': 'Full-stack dynamic web portal with role-based access control, relational database management (WAMP MySQL / PostgreSQL), administrative analytics, and CSRF protection.',
            'full_description': """### Service Overview
Designed for businesses needing custom internal tools, booking portals, customer dashboards, and inventory tracking systems with secure authentication and database persistence.""",
            'features': "Flask 3 backend with SQLAlchemy ORM\nRole-based user permissions (Admin, Customer, Staff)\nCSRF protected forms and secure session management\nCRUD management interfaces for all business records\nCSV/PDF export capabilities\nDual MySQL & SQLite compatibility",
            'deliverables': "Complete full-stack source code repository\nSQL schema and database seed scripts\nDeployment configuration for WAMP or cloud Linux server\nAdministrative training session",
            'project_requirements': "Specification of user roles, database entities, and key user flows.",
            'hosting_duration': 'Client hosting or quoted separately.',
            'domain_included': 'Client provided or quoted separately.',
            'renewal_cost': 'Optional ongoing maintenance agreement available.',
            'additional_charges': 'Third-party API integrations (SMS, Payment Gateways) quoted on requirement.',
            'is_published': True,
            'is_featured': False
        }
    ]

    for s in services_data:
        existing = Service.query.filter_by(slug=s['slug']).first()
        if not existing:
            serv = Service(
                title=s['title'],
                slug=s['slug'],
                starting_price=s['starting_price'],
                price_integer=s['price_integer'],
                timeline=s['timeline'],
                short_description=s['short_description'],
                full_description=s['full_description'],
                features=s['features'],
                deliverables=s['deliverables'],
                project_requirements=s['project_requirements'],
                hosting_duration=s['hosting_duration'],
                domain_included=s['domain_included'],
                renewal_cost=s['renewal_cost'],
                additional_charges=s['additional_charges'],
                is_published=s['is_published'],
                is_featured=s['is_featured']
            )
            db.session.add(serv)
        else:
            existing.starting_price = s['starting_price']
            existing.price_integer = s['price_integer']
            existing.timeline = s['timeline']
            existing.hosting_duration = s['hosting_duration']
            existing.domain_included = s['domain_included']
            existing.renewal_cost = s['renewal_cost']
            existing.additional_charges = s['additional_charges']

def seed_courses():
    courses_data = [
        {
            'title': 'C Programming',
            'slug': 'c-programming',
            'level': 'Beginner',
            'duration': '3 Weeks (18 Hours Live Mentoring)',
            'price': '₹599',
            'fee_integer': 599,
            'badge_text': 'Core Foundation',
            'is_featured': True,
            'delivery_mode': 'Online Live Mentoring',
            'class_schedule': 'Weekend & Evening Batches Available',
            'teaching_format': 'Live Screen-Share, Code Reviews & Logic Building Tasks',
            'status': 'Enrolling',
            'short_description': 'Master foundational programming concepts in C: variables, control structures, pointers, memory allocation, arrays, and structured algorithm design.',
            'syllabus': """Module 1: Introduction to C & Compilation | C syntax, compilers (GCC), data types, operators, and memory representation.
Module 2: Flow Control & Logic | Conditionals, switch-case, while, for loops, and nested logic patterns.
Module 3: Functions & Recursion | Function declarations, pass by value, call stack, and recursive algorithms.
Module 4: Arrays, Strings & Memory | 1D and 2D arrays, string manipulation, and standard string library.
Module 5: Pointers & Dynamic Memory | Pointer arithmetic, dereferencing, malloc(), free(), and avoiding memory leaks.
Module 6: Structures & File I/O | Structs, unions, file reading/writing, and capstone console project.""",
            'outcomes': """Understand low-level memory layout and pointer mechanics.
Write efficient, modular C programs independently.
Debug segmentation faults and memory leaks.
Build strong foundations for C++ and Python.""",
            'prerequisites': 'No prior coding experience required. Basic computer literacy.'
        },
        {
            'title': 'C++ Programming',
            'slug': 'cpp-programming',
            'level': 'Beginner to Intermediate',
            'duration': '4 Weeks (24 Hours Live Mentoring)',
            'price': '₹699',
            'fee_integer': 699,
            'badge_text': 'OOP & Performance',
            'is_featured': True,
            'delivery_mode': 'Online Live Mentoring',
            'class_schedule': 'Weekend & Evening Batches Available',
            'teaching_format': 'Live Screen-Share & Code Review',
            'status': 'Enrolling',
            'short_description': 'Object-Oriented Programming with C++: classes, inheritance, polymorphism, templates, standard template library (STL), and competitive coding concepts.',
            'syllabus': """Module 1: Transitioning to C++ | Namespaces, I/O streams, references vs pointers, and const correctness.
Module 2: Classes & Object-Oriented Design | Constructors, destructors, access specifiers, and operator overloading.
Module 3: Inheritance & Polymorphism | Base and derived classes, virtual functions, abstract classes, and vtables.
Module 4: Templates & Generic Code | Function templates, class templates, and generic data structures.
Module 5: Standard Template Library (STL) | Vectors, lists, maps, sets, iterators, and sorting algorithms.
Module 6: Capstone OOP Simulation Project | Building a multi-class management application.""",
            'outcomes': """Master OOP design principles in modern C++.
Utilize the C++ Standard Template Library (STL) effectively.
Design robust object hierarchies with inheritance and virtual methods.""",
            'prerequisites': 'Basic understanding of C syntax or general programming fundamentals.'
        },
        {
            'title': 'Python Programming',
            'slug': 'python-programming',
            'level': 'Comprehensive',
            'duration': '4 Weeks (24 Hours Live Mentoring)',
            'price': '₹899',
            'fee_integer': 899,
            'badge_text': 'Most Popular',
            'is_featured': True,
            'delivery_mode': 'Online Live Mentoring',
            'class_schedule': 'Weekend & Evening Batches Available',
            'teaching_format': 'Hands-on Live Coding & Mini-Project Mentorship',
            'status': 'Enrolling',
            'short_description': 'Complete practical Python engineering from syntax and data structures to object-oriented programming, file processing, and capstone mini-project development.',
            'syllabus': """Module 1: Python Fundamentals | Setup, Python 3.13 syntax, dynamic typing, variables, and operators.
Module 2: Control Flow & Iteration | Conditionals, while loops, for loops, and comprehension techniques.
Module 3: Core Data Structures | Lists, tuples, sets, dictionaries, and nested data manipulation.
Module 4: Functions & Modular Design | Parameter scoping, kwargs, lambda functions, and module importing.
Module 5: Object-Oriented Python | Classes, instances, dunder methods, inheritance, and clean code.
Module 6: File Handling & SQLite Database | Reading/writing CSVs, JSON, connecting to SQLite, and capstone project.""",
            'outcomes': """Write clean, idiomatic Python code following PEP 8.
Solve computational problems and build practical automation tools.
Work comfortably with relational databases and file inputs.
Build a complete working Python mini-project for your portfolio.""",
            'prerequisites': 'No prior coding experience required.'
        },
        {
            'title': 'HTML and CSS',
            'slug': 'html-and-css',
            'level': 'Beginner',
            'duration': '2 Weeks (12 Hours Live Mentoring)',
            'price': '₹499',
            'fee_integer': 499,
            'badge_text': 'Web Basics',
            'is_featured': False,
            'delivery_mode': 'Online Live Mentoring',
            'class_schedule': 'Flexible Weekend Batches',
            'teaching_format': 'Visual Live Styling & Responsive Layout Building',
            'status': 'Enrolling',
            'short_description': 'Learn semantic HTML5 markup and modern CSS3 styling: Flexbox, CSS Grid, media queries, typography, and responsive webpage design.',
            'syllabus': """Module 1: Semantic HTML5 | Document structure, headings, forms, tables, accessibility, and SEO tags.
Module 2: CSS Fundamentals | Selectors, the Box Model, borders, padding, margins, and typography.
Module 3: Modern Layouts with Flexbox | Flex containers, alignment, ordering, and responsive navigation bars.
Module 4: CSS Grid & Positioning | Multi-column layouts, relative/absolute positioning, and z-index.
Module 5: Responsive Design & Media Queries | Mobile-first design, breakpoints, and Bootstrap 5 basics.
Module 6: Capstone Landing Page | Building a responsive portfolio landing page from scratch.""",
            'outcomes': """Build clean, responsive web pages that look great on phones and desktops.
Master modern CSS Flexbox and Grid layouts.
Understand web accessibility and semantic markup.""",
            'prerequisites': 'Basic computer familiarity.'
        },
        {
            'title': 'JavaScript',
            'slug': 'javascript',
            'level': 'Beginner to Intermediate',
            'duration': '2 Weeks (12 Hours Live Mentoring)',
            'price': '₹299',
            'fee_integer': 299,
            'badge_text': 'Fast Track',
            'is_featured': True,
            'delivery_mode': 'Online Live Mentoring',
            'class_schedule': 'Weekend & Evening Batches',
            'teaching_format': 'Interactive DOM Manipulation & Event Handling',
            'status': 'Enrolling',
            'short_description': 'Dynamic frontend programming with JavaScript: ES6 syntax, DOM manipulation, event listeners, form validation, and asynchronous Fetch API.',
            'syllabus': """Module 1: Modern JavaScript Basics | Variables (let/const), data types, functions, and arrow syntax.
Module 2: DOM Manipulation | Selecting elements, modifying text/styles, and dynamic element creation.
Module 3: Events & User Interaction | Click, submit, input events, event bubbling, and form validation.
Module 4: Array Methods & ES6 Features | map, filter, reduce, destructuring, and template literals.
Module 5: Asynchronous JS & Fetch API | Promises, async/await, fetching JSON data from REST APIs.
Module 6: Capstone Dynamic Widget | Building an interactive task manager with LocalStorage persistence.""",
            'outcomes': """Add rich interactivity to static HTML/CSS web pages.
Validate forms dynamically on the client side.
Fetch data from public APIs and update the UI asynchronously.""",
            'prerequisites': 'Basic familiarity with HTML and CSS.'
        },
        {
            'title': 'PHP and MySQL',
            'slug': 'php-and-mysql',
            'level': 'Intermediate',
            'duration': '4 Weeks (24 Hours Live Mentoring)',
            'price': '₹1,499',
            'fee_integer': 1499,
            'badge_text': 'Database Web Apps',
            'is_featured': False,
            'delivery_mode': 'Online Live Mentoring',
            'class_schedule': 'Weekend Batches Available',
            'teaching_format': 'Server-Side Coding on WAMP Server',
            'status': 'Enrolling',
            'short_description': 'Server-side dynamic web development using PHP 8 and MySQL via WAMP: database connections, PDO, prepared statements, user sessions, and CRUD operations.',
            'syllabus': """Module 1: WAMP Server & PHP Basics | Local server configuration, phpMyAdmin, variables, and superglobals.
Module 2: Form Handling & Sanitization | POST/GET requests, validation, and preventing XSS.
Module 3: MySQL Relational Databases | Tables, relationships, foreign keys, and SQL queries.
Module 4: Secure Database Connection via PDO | Prepared statements, parameterized queries, and SQL injection defense.
Module 5: User Authentication & Sessions | Password hashing, session cookies, and login/logout flows.
Module 6: Capstone Database Portal | Complete CRUD business application with an admin panel.""",
            'outcomes': """Build complete database-driven web portals locally with WAMP.
Write secure PHP database queries using PDO.
Implement secure session-based authentication.""",
            'prerequisites': 'Basic HTML and CSS knowledge.'
        },
        {
            'title': 'Data Analysis',
            'slug': 'data-analysis',
            'level': 'Intermediate',
            'duration': '4 Weeks (24 Hours Live Mentoring)',
            'price': '₹1,499',
            'fee_integer': 1499,
            'badge_text': 'Business Analytics',
            'is_featured': False,
            'delivery_mode': 'Online Live Mentoring',
            'class_schedule': 'Weekend Batches Available',
            'teaching_format': 'Hands-on Data Wrangling with Pandas & Jupyter',
            'status': 'Enrolling',
            'short_description': 'Practical data analysis with Python: Pandas dataframes, NumPy arrays, data cleaning, aggregation, exploratory data analysis (EDA), and Matplotlib visualization.',
            'syllabus': """Module 1: Environment & NumPy Fundamentals | Jupyter Notebooks, vectorized arrays, indexing, and statistics.
Module 2: Pandas DataFrames | Loading CSV/Excel data, filtering rows, handling missing values, and column transforms.
Module 3: Data Aggregation & Grouping | GroupBy operations, pivot tables, multi-indexing, and merges/joins.
Module 4: Exploratory Data Analysis (EDA) | Statistical summaries, detecting outliers, and data distributions.
Module 5: Data Visualization | Line charts, bar plots, scatter plots, and heatmaps with Matplotlib and Seaborn.
Module 6: Real-World Dataset Project | Comprehensive business dataset analysis and insight report.""",
            'outcomes': """Clean and transform messy real-world datasets using Pandas.
Extract business insights through grouping and pivot operations.
Generate clear visual charts to communicate findings.""",
            'prerequisites': 'Basic Python programming knowledge.'
        },
        {
            'title': 'Data Science',
            'slug': 'data-science',
            'level': 'Advanced Track',
            'duration': '5 Weeks (30 Hours Live Mentoring)',
            'price': '₹999',
            'fee_integer': 999,
            'badge_text': 'Predictive Modeling',
            'is_featured': True,
            'delivery_mode': 'Online Live Mentoring',
            'class_schedule': 'Weekend & Evening Batches Available',
            'teaching_format': 'Practical Machine Learning with Scikit-Learn',
            'status': 'Enrolling',
            'short_description': 'Core Data Science workflows: feature engineering, train-test splitting, regression, classification, clustering, model evaluation metrics, and scikit-learn.',
            'syllabus': """Module 1: Foundations of Data Science | The ML workflow, hypothesis testing, and feature types.
Module 2: Feature Engineering & Preprocessing | One-hot encoding, feature scaling (StandardScaler), and handling missing data.
Module 3: Supervised Learning: Regression | Linear regression, cost functions, evaluation (MSE, R2 score).
Module 4: Supervised Learning: Classification | Logistic regression, Decision Trees, Random Forests, accuracy, precision/recall, and ROC-AUC.
Module 5: Unsupervised Learning | K-Means clustering and dimensionality reduction basics.
Module 6: Capstone Predictive Modeling Project | End-to-end dataset prediction pipeline and model persistence.""",
            'outcomes': """Train and evaluate supervised machine learning models.
Understand feature engineering and model evaluation metrics.
Build reproducible ML pipelines in Python.""",
            'prerequisites': 'Python fundamentals and basic data analysis knowledge.'
        },
        {
            'title': 'Artificial Intelligence',
            'slug': 'artificial-intelligence',
            'level': 'Intermediate to Advanced',
            'duration': '4 Weeks (24 Hours Live Mentoring)',
            'price': '₹999',
            'fee_integer': 999,
            'badge_text': 'Modern AI',
            'is_featured': False,
            'delivery_mode': 'Online Live Mentoring',
            'class_schedule': 'Weekend Batches Available',
            'teaching_format': 'Conceptual & Applied AI Algorithms in Python',
            'status': 'Enrolling',
            'short_description': 'Introduction to Artificial Intelligence: search algorithms, heuristic optimization, neural network foundations, natural language processing (NLP), and AI ethics.',
            'syllabus': """Module 1: Introduction to AI | History, state space representation, agent architectures, and problem-solving.
Module 2: Search Algorithms & Heuristics | Breadth-First, Depth-First, and A* heuristic search.
Module 3: Game Playing & Adversarial Search | Minimax algorithm, alpha-beta pruning, and decision trees.
Module 4: Neural Network Fundamentals | Perceptrons, activation functions, forward propagation, and backpropagation basics.
Module 5: Natural Language Processing (NLP) Basics | Tokenization, TF-IDF, sentiment analysis, and LLM prompting concepts.
Module 6: Capstone AI Application | Building a rule-based expert system or NLP text classifier.""",
            'outcomes': """Understand fundamental AI search and reasoning algorithms.
Grasp neural network architectures and learning mechanics.
Apply NLP techniques to analyze text datasets.""",
            'prerequisites': 'Solid Python programming and basic math concepts.'
        },
        {
            'title': 'Cybersecurity Fundamentals',
            'slug': 'cybersecurity-fundamentals',
            'level': 'Beginner to Intermediate',
            'duration': '3 Weeks (18 Hours Live Mentoring)',
            'price': '₹899',
            'fee_integer': 899,
            'badge_text': 'Security Essentials',
            'is_featured': False,
            'delivery_mode': 'Online Live Mentoring',
            'class_schedule': 'Weekend & Evening Batches Available',
            'teaching_format': 'Defensive Security & Threat Modeling Labs',
            'status': 'Enrolling',
            'short_description': 'Essential cybersecurity concepts: OWASP Top 10 vulnerabilities, web security defenses, cryptography basics, authentication protocols, and secure coding practices.',
            'syllabus': """Module 1: Security Fundamentals & Threat Landscape | Confidentiality, Integrity, Availability (CIA Triad), and attack surfaces.
Module 2: Network Security & Protocols | IP, TCP/UDP, DNS, HTTPS/TLS, firewalls, and port scanning concepts.
Module 3: Cryptography & Hashing | Symmetric vs asymmetric encryption, RSA, SHA-256 hashing, and salt mechanics.
Module 4: Web Application Security (OWASP Top 10) | SQL injection, XSS, CSRF, broken access control, and defensive mitigation.
Module 5: Authentication & Defense-in-Depth | Password storage, Multi-Factor Authentication (MFA/TOTP), and session management.
Module 6: Capstone Secure Coding Audit | Performing a defensive security review of a vulnerable Python web app.""",
            'outcomes': """Identify common web application vulnerabilities (OWASP Top 10).
Implement secure coding standards and defenses in Python web apps.
Understand cryptographic principles and safe password handling.""",
            'prerequisites': 'Basic computer networking and programming concepts.'
        }
    ]

    for c in courses_data:
        existing = Course.query.filter_by(slug=c['slug']).first()
        if not existing:
            course = Course(
                title=c['title'],
                slug=c['slug'],
                level=c['level'],
                duration=c['duration'],
                price=c['price'],
                fee_integer=c['fee_integer'],
                badge_text=c['badge_text'],
                is_featured=c['is_featured'],
                delivery_mode=c['delivery_mode'],
                class_schedule=c['class_schedule'],
                teaching_format=c['teaching_format'],
                status=c['status'],
                short_description=c['short_description'],
                syllabus=c['syllabus'],
                outcomes=c['outcomes'],
                prerequisites=c['prerequisites'],
                is_published=True
            )
            db.session.add(course)
        else:
            existing.price = c['price']
            existing.fee_integer = c['fee_integer']
            existing.delivery_mode = c['delivery_mode']
            existing.class_schedule = c['class_schedule']
            existing.teaching_format = c['teaching_format']
            existing.status = c['status']

def seed_portfolio():
    portfolio_items = [
        {
            'title': 'Bitetech Dynamic Platform & CMS',
            'category': 'Full-Stack Web App',
            'description': 'The core website and admin portal for Bitetech Technologies built with Python Flask, SQLAlchemy, CSRF security, and modular templates.',
            'client_type': 'Internal Platform & Reference Architecture',
            'features': "Dynamic enquiry routing and CSV exports\nRole-based administrative management\nDual database compatibility (MySQL / SQLite)\nResponsive mobile-first layout",
            'technologies': 'Python 3.13, Flask, SQLAlchemy, MySQL, Bootstrap 5',
            'live_url': 'http://127.0.0.1:5000',
            'is_published': True
        },
        {
            'title': 'Small Business Retail Showcase Website',
            'category': 'Website Development',
            'description': 'A responsive, high-speed business showcase website with product highlights, WhatsApp lead generation, and Google Maps integration.',
            'client_type': 'Small Business Client Reference',
            'features': "Fast-loading mobile-first Bootstrap layout\nDirect WhatsApp lead generation integration\nProduct catalog with category navigation\nCustom contact forms with CSRF validation",
            'technologies': 'HTML5, CSS3, JavaScript, Bootstrap 5, Flask',
            'live_url': '#',
            'is_published': True
        },
        {
            'title': 'Inventory & Stock Reconciliation System',
            'category': 'Database Management',
            'description': 'Demonstration inventory management portal supporting barcode tracking, low stock alerts, and automated reorder calculations.',
            'client_type': 'Engineering Demonstration',
            'features': "SKU tracking and inventory ledger\nAutomated minimum stock alerts\nSupplier and purchase order ledger\nRelational MySQL backend",
            'technologies': 'Python, Flask, PyMySQL, Bootstrap 5',
            'live_url': '#',
            'is_published': True
        },
        {
            'title': 'Automated Multi-Source Data Parser',
            'category': 'Automation & Scripting',
            'description': 'Scheduled Python automation worker that scrapes public technical data, sanitizes inputs, and generates styled daily Excel spreadsheets.',
            'client_type': 'Technical Reference Project',
            'features': "Automated hourly web scrapers\nContent deduplication and text normalization\nAutomated multi-tab Excel spreadsheet generation\nError recovery and respectful rate limiting",
            'technologies': 'Python 3, BeautifulSoup4, Requests, SQLite, OpenPyXL',
            'live_url': '#',
            'is_published': True
        }
    ]

    for item in portfolio_items:
        if not PortfolioItem.query.filter_by(title=item['title']).first():
            p_item = PortfolioItem(
                title=item['title'],
                category=item['category'],
                description=item['description'],
                client_type=item['client_type'],
                features=item['features'],
                technologies=item['technologies'],
                live_url=item['live_url'],
                is_published=item['is_published']
            )
            db.session.add(p_item)

def seed_faqs():
    faqs = [
        ('What is Bitetech Technologies?', 'Bitetech Technologies is a specialized software development and training initiative focused on Python development projects, custom website development, and live, mentor-led online programming classes. We provide students, creators, and small businesses with clean, functional code and practical engineering guidance.', 'General', 1),
        ('How much do Python mini projects cost?', 'Our Python mini-projects start at just ₹599, and major projects start at ₹1,000, depending on project complexity, database requirements, and documentation needs. We provide transparent upfront pricing before starting any work.', 'Projects', 2),
        ('How much does website development cost?', 'Our Shop or Small Business Website starts at ₹5,000, and our turnkey Website with Hosting package starts at ₹7,000. These are starting baseline estimates; final quotations depend on specific requirements and are approved before any billing.', 'Services & Hosting', 3),
        ('What is included in the ₹7,000 Website with Hosting package?', 'It includes custom responsive website development (up to 6 pages), 1-year shared cloud hosting, assistance with domain registration (.com or .in for year 1), free SSL certificate, and business email setup. Renewal costs in subsequent years are estimated at ₹2,500/year.', 'Services & Hosting', 4),
        ('Are reference projects ready to run immediately?', 'Yes. All reference projects developed by Bitetech Technologies include clear installation instructions, database setup scripts (for both SQLite and WAMP MySQL), and verified dependency files so you can run them immediately on Windows or Linux.', 'Projects', 5),
        ('Do you offer live classes or pre-recorded sessions?', 'We primarily offer live, interactive online mentoring sessions with screen sharing, code reviews, and hands-on coding exercises. Weekend and evening batches are available to accommodate student and working schedules.', 'Classes', 6),
        ('Do you guarantee jobs or issue official university degrees?', 'No. We believe in complete honesty and transparency: our courses focus on hands-on coding skills, logic building, and verifiable portfolio projects. We do not make false claims of university accreditation or legally guaranteed employment.', 'Classes', 7),
        ('How do I receive project files after ordering?', 'Project source code, database scripts, and setup guides are delivered directly via secure download link or email. We also provide initial setup assistance over WhatsApp or screen share if needed.', 'Payments & Support', 8),
        ('What is your refund policy?', 'We offer refunds prior to the delivery of custom source code or before online class batches start. Because digital code is completely accessible once delivered, refunds cannot be issued after full source code handoff. See our full Refund and Cancellation Policy page.', 'Payments & Support', 9),
        ('How can I contact Bitetech Technologies directly?', 'You can reach us at bitetechtechnologies@gmail.com, call 7418332912, or message us directly on WhatsApp using the button on our website.', 'General', 10)
    ]

    for q, a, cat, order in faqs:
        if not FAQ.query.filter_by(question=q).first():
            faq_obj = FAQ(question=q, answer=a, category=cat, display_order=order, is_published=True)
            db.session.add(faq_obj)

def seed_sample_enquiries():
    admin = User.query.filter_by(role='admin').first()
    student = User.query.filter_by(role='customer').first()

    if ProjectEnquiry.query.count() == 0:
        p1 = Project.query.first()
        sample_pe = ProjectEnquiry(
            project_id=p1.id if p1 else None,
            user_id=student.id if student else None,
            client_name='Aarav Mehta',
            client_email='student@example.com',
            client_phone='9876543210',
            project_type='Customization of Existing Demo',
            budget_range='₹599 - ₹1,000',
            requirements='Need student attendance tracker customized with additional roll number search and CSV report export for college project submission.',
            status='New'
        )
        db.session.add(sample_pe)

    if CourseEnquiry.query.count() == 0:
        c1 = Course.query.filter_by(slug='python-programming').first()
        sample_ce = CourseEnquiry(
            course_id=c1.id if c1 else None,
            user_id=student.id if student else None,
            student_name='Aarav Mehta',
            student_email='student@example.com',
            student_phone='9876543210',
            preferred_batch='Weekend Batches (Sat-Sun)',
            learning_mode='Online Live Mentoring',
            message='Looking forward to mastering Python logic and algorithms from basics.',
            status='Contacted',
            admin_notes='Sent batch schedule and introductory syllabus via WhatsApp.'
        )
        db.session.add(sample_ce)

    if ServiceEnquiry.query.count() == 0:
        s1 = Service.query.first()
        sample_se = ServiceEnquiry(
            service_id=s1.id if s1 else None,
            user_id=student.id if student else None,
            client_name='Rohan Sharma',
            client_email='rohan@example.com',
            client_phone='9812345678',
            project_title='Retail Grocery Store Showcase Website',
            budget_range='₹5,000 - ₹7,000',
            project_requirements='Need a clean 5-page shop website with grocery catalog, store timings, WhatsApp order button, and Google Maps location.',
            target_timeline='Within 10 Days',
            status='New'
        )
        db.session.add(sample_se)

    if ContactMessage.query.count() == 0:
        sample_cm = ContactMessage(
            user_id=student.id if student else None,
            name='Neha Kapoor',
            email='neha@example.com',
            phone='7890123456',
            subject='Inquiry about Python Major Project development',
            service='Python Major Project Development',
            budget='₹1,000 - ₹2,500',
            message='Looking for guidance and source code for a hospital appointment portal with WAMP MySQL backend.',
            status='New'
        )
        db.session.add(sample_cm)

if __name__ == '__main__':
    init_database()
