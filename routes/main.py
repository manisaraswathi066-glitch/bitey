import secrets
from datetime import datetime, timezone, timedelta
from flask import render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from routes import main_bp
from extensions import db
from models import (
    User, Project, ProjectCategory, Course, Service, PortfolioItem, 
    FAQ, SiteSetting, ContactMessage, ProjectEnquiry, CourseEnquiry, 
    ServiceEnquiry, ProjectOrder, PasswordResetToken
)
from forms import (
    ContactForm, ProjectEnquiryForm, CourseEnquiryForm, ServiceEnquiryForm,
    CustomerLoginForm, CustomerRegistrationForm, ForgotPasswordRequestForm,
    ResetPasswordForm, CustomerProfileForm
)
from security import limiter, get_incident_mode, get_client_ip, log_security_event, is_safe_url

def check_form_security():
    """
    Validates that:
    1. The platform is not in maintenance/read-only or lockdown mode.
    2. The submitting IP address has not exceeded rolling submission limits.
    """
    if get_incident_mode() in ('read_only', 'lockdown'):
        flash("Bitetech platform is currently in maintenance / defensive mode. Direct web form submissions are temporarily paused. Please reach out to us directly via WhatsApp at +91 7418332912 or email bitetechtechnologies@gmail.com.", "warning")
        return False

    ip = get_client_ip()
    allowed, retry_after = limiter.is_allowed(f"form_submit_{ip}", 25, 600)
    if not allowed:
        log_security_event('FORM_RATE_LIMITED', details=f"IP {ip} exceeded form limit", status='WARNING')
        flash(f"You have submitted multiple requests recently. Please wait {retry_after} second(s) before submitting again, or connect via WhatsApp.", "warning")
        return False

    return True

# ---------------------------------------------------------------------------
# PUBLIC PAGES
# ---------------------------------------------------------------------------

@main_bp.route('/')
@main_bp.route('/api/index.py')
@main_bp.route('/api/index')
def index():
    mini_projects = Project.query.filter_by(is_published=True, project_type='Mini').order_by(Project.is_featured.desc(), Project.created_at.desc()).limit(3).all()
    major_projects = Project.query.filter_by(is_published=True, project_type='Major').order_by(Project.is_featured.desc(), Project.created_at.desc()).limit(3).all()
    if not mini_projects and not major_projects:
        featured_projects = Project.query.filter_by(is_published=True).order_by(Project.is_featured.desc(), Project.created_at.desc()).limit(6).all()
    else:
        featured_projects = mini_projects + major_projects

    services = Service.query.filter_by(is_published=True).order_by(Service.is_featured.desc(), Service.price_integer.asc()).limit(4).all()
    courses = Course.query.filter_by(is_published=True).order_by(Course.is_featured.desc(), Course.fee_integer.asc()).limit(4).all()
    faqs = FAQ.query.filter_by(is_published=True).order_by(FAQ.display_order.asc(), FAQ.id.asc()).limit(5).all()
    categories = ProjectCategory.query.all()
    contact_form = ContactForm()
    
    return render_template(
        'index.html',
        featured_projects=featured_projects,
        mini_projects=mini_projects,
        major_projects=major_projects,
        services=services,
        courses=courses,
        faqs=faqs,
        categories=categories,
        contact_form=contact_form,
        incident_mode=get_incident_mode()
    )

@main_bp.route('/about')
def about():
    about_text = SiteSetting.get_setting('about_text', '')
    mission_text = SiteSetting.get_setting('mission_text', '')
    vision_text = SiteSetting.get_setting('vision_text', '')
    return render_template(
        'about.html',
        about_text=about_text,
        mission_text=mission_text,
        vision_text=vision_text
    )

@main_bp.route('/projects')
def projects(forced_type=None):
    category_slug = request.args.get('category', '').strip()
    project_type = forced_type or request.args.get('type', '').strip().capitalize()  # 'Mini' or 'Major'
    search_query = request.args.get('q', '').strip()[:100]
    sort_by = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    
    query = Project.query.filter_by(is_published=True)
    
    selected_category = None
    if category_slug:
        selected_category = ProjectCategory.query.filter_by(slug=category_slug).first()
        if selected_category:
            query = query.filter_by(category_id=selected_category.id)
            
    if project_type in ('Mini', 'Major'):
        query = query.filter_by(project_type=project_type)

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.filter(
            (Project.title.ilike(like_pattern)) | 
            (Project.short_description.ilike(like_pattern)) | 
            (Project.tech_stack.ilike(like_pattern))
        )
        
    if sort_by == 'price_asc':
        query = query.order_by(Project.starting_price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Project.starting_price.desc())
    else:
        query = query.order_by(Project.created_at.desc())

    projects_pagination = query.paginate(
        page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 9), error_out=False
    )
    categories = ProjectCategory.query.all()
    
    return render_template(
        'projects.html',
        projects=projects_pagination.items,
        pagination=projects_pagination,
        categories=categories,
        selected_category=selected_category,
        selected_type=project_type,
        search_query=search_query,
        sort_by=sort_by
    )

@main_bp.route('/projects/mini')
def projects_mini():
    """Dedicated catalog route for Python Mini Projects (Starts ₹599)."""
    return projects(forced_type='Mini')

@main_bp.route('/projects/major')
def projects_major():
    """Dedicated catalog route for Python Major Projects (Starts ₹1,000)."""
    return projects(forced_type='Major')

@main_bp.route('/projects/<slug>', methods=['GET', 'POST'])
def project_detail(slug):
    project = Project.query.filter_by(slug=slug, is_published=True).first_or_404()
    form = ProjectEnquiryForm(project_id=project.id)
    
    # Pre-fill user data if logged in
    if request.method == 'GET' and current_user.is_authenticated:
        if not form.client_name.data:
            form.client_name.data = current_user.full_name or current_user.username
        if not form.client_email.data:
            form.client_email.data = current_user.email
        if not form.client_phone.data and current_user.phone:
            form.client_phone.data = current_user.phone

    if form.validate_on_submit():
        if not check_form_security():
            return redirect(url_for('main.project_detail', slug=slug))

        if form.website_hp.data:
            flash("Thank you for your enquiry. We will review your request shortly.", "success")
            return redirect(url_for('main.project_detail', slug=slug))
            
        user_id = current_user.id if current_user.is_authenticated else None
        if not user_id:
            existing_user = User.query.filter_by(email=form.client_email.data.strip().lower()).first()
            if existing_user:
                user_id = existing_user.id

        enquiry = ProjectEnquiry(
            project_id=project.id,
            user_id=user_id,
            client_name=form.client_name.data.strip()[:120],
            client_email=form.client_email.data.strip().lower()[:120],
            client_phone=form.client_phone.data.strip()[:30],
            project_type=form.project_type.data[:100],
            budget_range=form.budget_range.data[:100],
            requirements=form.requirements.data.strip()[:3000],
            status='New'
        )
        db.session.add(enquiry)
        db.session.commit()
        
        flash("Thank you! Your project enquiry has been submitted. Our development team will review it and get back to you via email or WhatsApp within 24 hours.", "success")
        return redirect(url_for('main.project_detail', slug=slug))
        
    related_projects = Project.query.filter(
        Project.id != project.id,
        Project.category_id == project.category_id,
        Project.is_published == True
    ).limit(3).all()
    
    return render_template(
        'project_detail.html',
        project=project,
        form=form,
        related_projects=related_projects,
        incident_mode=get_incident_mode()
    )

@main_bp.route('/services')
def services():
    services_list = Service.query.filter_by(is_published=True).order_by(Service.price_integer.asc()).all()
    enquiry_form = ServiceEnquiryForm()
    return render_template('services.html', services=services_list, form=enquiry_form, incident_mode=get_incident_mode())

@main_bp.route('/services/<slug>', methods=['GET', 'POST'])
def service_detail(slug):
    service = Service.query.filter_by(slug=slug, is_published=True).first_or_404()
    form = ServiceEnquiryForm(service_id=service.id)
    
    if request.method == 'GET' and current_user.is_authenticated:
        if not form.client_name.data:
            form.client_name.data = current_user.full_name or current_user.username
        if not form.client_email.data:
            form.client_email.data = current_user.email
        if not form.client_phone.data and current_user.phone:
            form.client_phone.data = current_user.phone

    if form.validate_on_submit():
        if not check_form_security():
            return redirect(url_for('main.service_detail', slug=slug))

        if form.website_hp.data:
            flash("Quotation request submitted successfully.", "success")
            return redirect(url_for('main.service_detail', slug=slug))

        user_id = current_user.id if current_user.is_authenticated else None
        if not user_id:
            existing_user = User.query.filter_by(email=form.client_email.data.strip().lower()).first()
            if existing_user:
                user_id = existing_user.id

        enquiry = ServiceEnquiry(
            service_id=service.id,
            user_id=user_id,
            client_name=form.client_name.data.strip()[:120],
            client_email=form.client_email.data.strip().lower()[:120],
            client_phone=form.client_phone.data.strip()[:30],
            project_title=form.project_title.data.strip()[:200],
            budget_range=form.budget_range.data[:100],
            project_requirements=form.project_requirements.data.strip()[:3000],
            target_timeline=form.target_timeline.data.strip()[:100] if form.target_timeline.data else 'Standard',
            status='New'
        )
        db.session.add(enquiry)
        db.session.commit()

        flash(f"Thank you! Your quotation enquiry for '{service.title}' has been submitted. Our technical team will prepare a formal proposal.", "success")
        return redirect(url_for('main.service_detail', slug=slug))

    other_services = Service.query.filter(Service.id != service.id, Service.is_published == True).limit(3).all()
    return render_template('service_detail.html', service=service, form=form, other_services=other_services, incident_mode=get_incident_mode())

@main_bp.route('/courses')
def courses():
    courses_list = Course.query.filter_by(is_published=True).order_by(Course.is_featured.desc(), Course.fee_integer.asc()).all()
    enquiry_form = CourseEnquiryForm()
    return render_template('courses.html', courses=courses_list, form=enquiry_form, incident_mode=get_incident_mode())

@main_bp.route('/courses/<slug>', methods=['GET', 'POST'])
def course_detail(slug):
    course = Course.query.filter_by(slug=slug, is_published=True).first_or_404()
    form = CourseEnquiryForm(course_id=course.id)
    
    if request.method == 'GET' and current_user.is_authenticated:
        if not form.student_name.data:
            form.student_name.data = current_user.full_name or current_user.username
        if not form.student_email.data:
            form.student_email.data = current_user.email
        if not form.student_phone.data and current_user.phone:
            form.student_phone.data = current_user.phone

    if form.validate_on_submit():
        if not check_form_security():
            return redirect(url_for('main.course_detail', slug=slug))

        if form.website_hp.data:
            flash("Enrollment request received successfully.", "success")
            return redirect(url_for('main.course_detail', slug=slug))
            
        user_id = current_user.id if current_user.is_authenticated else None
        if not user_id:
            existing_user = User.query.filter_by(email=form.student_email.data.strip().lower()).first()
            if existing_user:
                user_id = existing_user.id

        enquiry = CourseEnquiry(
            course_id=course.id,
            user_id=user_id,
            student_name=form.student_name.data.strip()[:120],
            student_email=form.student_email.data.strip().lower()[:120],
            student_phone=form.student_phone.data.strip()[:30],
            preferred_batch=form.preferred_batch.data[:50],
            learning_mode=form.learning_mode.data[:50] if hasattr(form, 'learning_mode') and form.learning_mode.data else 'Online Live',
            message=form.message.data.strip()[:1000] if form.message.data else '',
            status='New'
        )
        db.session.add(enquiry)
        db.session.commit()
        
        flash(f"Congratulations! Your registration interest for '{course.title}' has been received. Our course coordinator will connect with you with the syllabus and batch schedule.", "success")
        return redirect(url_for('main.course_detail', slug=slug))
        
    other_courses = Course.query.filter(Course.id != course.id, Course.is_published == True).limit(3).all()
    return render_template('course_detail.html', course=course, form=form, other_courses=other_courses, incident_mode=get_incident_mode())

@main_bp.route('/portfolio')
def portfolio():
    items = PortfolioItem.query.filter_by(is_published=True).order_by(PortfolioItem.created_at.desc()).all()
    categories = sorted(list({item.category for item in items if item.category}))
    return render_template('portfolio.html', items=items, categories=categories)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if request.method == 'GET' and current_user.is_authenticated:
        if not form.name.data:
            form.name.data = current_user.full_name or current_user.username
        if not form.email.data:
            form.email.data = current_user.email
        if not form.phone.data and current_user.phone:
            form.phone.data = current_user.phone

    if form.validate_on_submit():
        if not check_form_security():
            return redirect(url_for('main.contact'))

        if form.website_hp.data:
            flash("Thank you for reaching out. We will get back to you soon.", "success")
            return redirect(url_for('main.contact'))
            
        user_id = current_user.id if current_user.is_authenticated else None
        if not user_id:
            existing_user = User.query.filter_by(email=form.email.data.strip().lower()).first()
            if existing_user:
                user_id = existing_user.id

        msg = ContactMessage(
            user_id=user_id,
            name=form.name.data.strip()[:120],
            email=form.email.data.strip().lower()[:120],
            phone=form.phone.data.strip()[:30],
            subject=form.subject.data.strip()[:200],
            service=form.service.data[:100],
            budget=form.budget.data[:100],
            message=form.message.data.strip()[:3000],
            status='New'
        )
        db.session.add(msg)
        db.session.commit()
        
        flash("Thank you! Your message has been received. Our team will contact you promptly at " + form.email.data + " or via WhatsApp.", "success")
        return redirect(url_for('main.contact'))
        
    return render_template('contact.html', form=form, incident_mode=get_incident_mode())

@main_bp.route('/faq')
def faq():
    category = request.args.get('cat', '').strip()[:50]
    query = FAQ.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)
    faqs = query.order_by(FAQ.display_order.asc(), FAQ.id.asc()).all()
    categories = ['General', 'Projects', 'Classes', 'Services & Hosting', 'Payments & Support']
    return render_template('faq.html', faqs=faqs, categories=categories, selected_cat=category)

# ----------------- BUSINESS POLICIES -----------------

@main_bp.route('/privacy-policy')
def privacy_policy():
    policy_content = SiteSetting.get_setting('privacy_policy', '')
    return render_template('privacy_policy.html', content=policy_content)

@main_bp.route('/terms')
def terms():
    terms_content = SiteSetting.get_setting('terms_conditions', '')
    return render_template('terms.html', content=terms_content)

@main_bp.route('/refund-policy')
def refund_policy():
    refund_content = SiteSetting.get_setting('refund_policy', '')
    return render_template('refund_policy.html', content=refund_content)

@main_bp.route('/project-delivery-policy')
def project_delivery_policy():
    delivery_content = SiteSetting.get_setting('project_delivery_policy', '')
    return render_template('project_delivery_policy.html', content=delivery_content)

@main_bp.route('/hosting-renewal-policy')
def hosting_renewal_policy():
    hosting_content = SiteSetting.get_setting('hosting_renewal_policy', '')
    return render_template('hosting_renewal_policy.html', content=hosting_content)

# ---------------------------------------------------------------------------
# CUSTOMER AUTHENTICATION & DASHBOARD
# ---------------------------------------------------------------------------

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.dashboard'))

    form = CustomerLoginForm()
    ip = get_client_ip()

    allowed, retry_after = limiter.is_allowed(f"cust_login_{ip}", 12, 60)
    if not allowed:
        log_security_event('CUSTOMER_LOGIN_RATE_LIMITED', details=f"IP {ip} exceeded rate limit", status='WARNING')
        flash(f"Too many login attempts. Please wait {retry_after} seconds before trying again.", "danger")
        return render_template('login.html', form=form), 429

    if form.validate_on_submit():
        identifier = form.username_or_email.data.strip()
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        now = datetime.now(timezone.utc)
        if user and user.locked_until:
            locked_until = user.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if now < locked_until:
                remaining = int((locked_until - now).total_seconds() / 60)
                flash(f"Account temporarily locked due to failed attempts. Try again in {remaining + 1} minutes.", "danger")
                return render_template('login.html', form=form)
            else:
                user.locked_until = None
                user.failed_logins = 0
                db.session.commit()

        if user and user.is_active and user.check_password(form.password.data):
            user.failed_logins = 0
            user.locked_until = None
            user.last_login = now
            db.session.commit()

            login_user(user, remember=form.remember_me.data)
            log_security_event('CUSTOMER_LOGIN_SUCCESS', user=user)
            flash(f"Welcome back, {user.full_name or user.username}!", "success")

            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)

            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.dashboard'))
        else:
            if user:
                user.failed_logins = (user.failed_logins or 0) + 1
                if user.failed_logins >= 5:
                    user.locked_until = now + timedelta(minutes=15)
                    log_security_event('ACCOUNT_LOCKOUT_TRIGGERED', user=user, status='WARNING')
                    flash("Too many failed attempts. Account locked for 15 minutes.", "danger")
                db.session.commit()
            flash("Invalid email/username or password. Please try again.", "danger")

    return render_template('login.html', form=form)

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = CustomerRegistrationForm()
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        email = form.email.data.strip().lower()

        if User.query.filter_by(username=username).first():
            flash("This username is already taken. Please choose another.", "warning")
            return render_template('register.html', form=form)

        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists. Please sign in.", "warning")
            return redirect(url_for('main.login'))

        new_user = User(
            username=username,
            email=email,
            full_name=form.full_name.data.strip()[:100],
            phone=form.phone.data.strip()[:30],
            role='customer',
            is_active=True
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        # Link past enquiries submitted with this email to this user account
        ProjectEnquiry.query.filter_by(client_email=email, user_id=None).update({'user_id': new_user.id})
        CourseEnquiry.query.filter_by(student_email=email, user_id=None).update({'user_id': new_user.id})
        ServiceEnquiry.query.filter_by(client_email=email, user_id=None).update({'user_id': new_user.id})
        ContactMessage.query.filter_by(email=email, user_id=None).update({'user_id': new_user.id})
        db.session.commit()

        log_security_event('CUSTOMER_REGISTERED', user=new_user)
        login_user(new_user)
        flash("Your account has been created successfully! Welcome to Bitetech Technologies.", "success")
        return redirect(url_for('main.dashboard'))

    return render_template('register.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    log_security_event('USER_LOGOUT', user=current_user)
    logout_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('main.login'))

@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordRequestForm()
    reset_token_display = None

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = secrets.token_urlsafe(32)
            exp = datetime.now(timezone.utc) + timedelta(hours=2)
            prt = PasswordResetToken(user_id=user.id, token_hash=token, expires_at=exp)
            db.session.add(prt)
            db.session.commit()
            log_security_event('PASSWORD_RESET_TOKEN_GENERATED', user=user)

            # In development/local without SMTP configured, show instructions and token directly
            reset_token_display = token
            flash("Password reset instructions prepared. (For local development or when SMTP is unconfigured, use the secure link below).", "info")
        else:
            flash("If that email address is registered, password reset instructions have been generated.", "info")

    return render_template('forgot_password.html', form=form, reset_token=reset_token_display)

@main_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    token_record = PasswordResetToken.query.filter_by(token_hash=token, used=False).first()
    if not token_record or not token_record.is_valid():
        flash("The password reset link is invalid or has expired. Please request a new one.", "danger")
        return redirect(url_for('main.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = token_record.user
        user.set_password(form.password.data)
        user.failed_logins = 0
        user.locked_until = None
        token_record.used = True
        db.session.commit()

        log_security_event('PASSWORD_RESET_SUCCESS', user=user)
        flash("Your password has been reset successfully! You may now sign in.", "success")
        return redirect(url_for('main.login'))

    return render_template('reset_password.html', form=form, token=token)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Personal Customer & Student Dashboard (Strict record ownership)."""
    # Enquiries and requests submitted by or linked to current_user
    project_enquiries = ProjectEnquiry.query.filter_by(user_id=current_user.id).order_by(ProjectEnquiry.created_at.desc()).all()
    course_enquiries = CourseEnquiry.query.filter_by(user_id=current_user.id).order_by(CourseEnquiry.created_at.desc()).all()
    service_enquiries = ServiceEnquiry.query.filter_by(user_id=current_user.id).order_by(ServiceEnquiry.created_at.desc()).all()
    orders = ProjectOrder.query.filter_by(user_id=current_user.id).order_by(ProjectOrder.created_at.desc()).all()
    contact_messages = ContactMessage.query.filter_by(user_id=current_user.id).order_by(ContactMessage.created_at.desc()).all()

    profile_form = CustomerProfileForm(
        full_name=current_user.full_name or '',
        phone=current_user.phone or ''
    )

    return render_template(
        'dashboard.html',
        project_enquiries=project_enquiries,
        course_enquiries=course_enquiries,
        service_enquiries=service_enquiries,
        orders=orders,
        contact_messages=contact_messages,
        profile_form=profile_form
    )

@main_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    form = CustomerProfileForm()
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()[:100]
        current_user.phone = form.phone.data.strip()[:30]
        db.session.commit()
        flash("Your profile information has been updated.", "success")
    else:
        for field, errs in form.errors.items():
            for e in errs:
                flash(f"{field}: {e}", "danger")
    return redirect(url_for('main.dashboard', _anchor='profile-content'))
