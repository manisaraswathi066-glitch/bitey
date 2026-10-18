import csv
import io
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import (
    render_template, request, flash, redirect, 
    url_for, session, Response, current_app, abort
)
from flask_login import login_user, logout_user, current_user
from routes import admin_bp
from extensions import db
from models import (
    User, AdminUser, Project, ProjectCategory, Course, Service, 
    PortfolioItem, FAQ, SiteSetting, ContactMessage, ProjectEnquiry, 
    CourseEnquiry, ServiceEnquiry, ProjectOrder, AuditLog
)
from forms import (
    AdminLoginForm, ProjectForm, CourseForm, ServiceForm, PortfolioForm, 
    FAQForm, CategoryForm, SiteSettingsForm, MFAVerifyForm, 
    MFASetupForm, ConfirmPasswordForm
)
from security import (
    is_safe_url, limiter, log_security_event, 
    generate_totp_secret, get_totp_uri, verify_totp_code, 
    get_incident_mode, get_client_ip
)

# ----------------- SECURITY DECORATOR -----------------
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('admin_user_id')
        if not user_id and current_user.is_authenticated and current_user.is_admin:
            user_id = current_user.id
            session['admin_user_id'] = user_id
            session['admin_token_version'] = current_user.token_version

        if not user_id:
            flash("Please sign in with administrator credentials to access this portal.", "warning")
            return redirect(url_for('admin.login', next=request.url))
            
        user = db.session.get(User, user_id)
        if not user or not user.is_active or not user.is_admin:
            session.clear()
            logout_user()
            flash("Your administrative session is invalid or your account has been deactivated.", "danger")
            return redirect(url_for('admin.login'))
            
        # 1. Session Revocation Check (Token Version)
        if session.get('admin_token_version') != user.token_version:
            session.clear()
            flash("Your session has expired or was revoked by a security event. Please sign in again.", "warning")
            return redirect(url_for('admin.login'))

        # 2. Inactivity Timeout Check (30 minutes = 1800 seconds)
        last_active = session.get('last_active')
        now_ts = time.time()
        if last_active and (now_ts - last_active > 1800):
            session.clear()
            flash("Session expired due to 30 minutes of inactivity. Please re-authenticate.", "info")
            return redirect(url_for('admin.login'))
        session['last_active'] = now_ts

        # 3. Incident Response Mode Check
        if get_incident_mode() == 'lockdown' and user.role != 'superadmin':
            session.clear()
            flash("Emergency security lockdown is currently active. Administrative access is restricted.", "danger")
            return redirect(url_for('admin.login'))
            
        return f(*args, **kwargs)
    return decorated_function

# ----------------- AUTHENTICATION & MFA -----------------
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_user_id') and current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
        
    form = AdminLoginForm()
    ip = get_client_ip()

    # Rate Limiting: Max 10 login requests per minute per IP
    allowed, retry_after = limiter.is_allowed(f"admin_login_{ip}", 10, 60)
    if not allowed:
        log_security_event('LOGIN_RATE_LIMITED', details=f"IP {ip} exceeded rate limit", status='WARNING')
        flash(f"Too many login attempts. Please wait {retry_after} second(s) before trying again.", "danger")
        return render_template('admin/login.html', form=form), 429

    # Incident Response Lockdown Check
    if get_incident_mode() == 'lockdown':
        flash("Security Lockdown Active: Direct administrative web logins are temporarily disabled per incident response protocol.", "danger")
        return render_template('admin/login.html', form=form), 503
        
    if form.validate_on_submit():
        identifier = form.username.data.strip()
        user = User.query.filter(
            ((User.username == identifier) | (User.email == identifier.lower())) &
            (User.role.in_(['admin', 'superadmin']))
        ).first()
        
        now = datetime.now(timezone.utc)
        
        # Check Account Lockout
        if user and user.locked_until:
            locked_until = user.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if now < locked_until:
                remaining = int((locked_until - now).total_seconds() / 60)
                log_security_event('LOGIN_LOCKED_ATTEMPT', user=user, details=f"Attempt while locked for {remaining+1}m", status='WARNING')
                flash(f"Account is temporarily locked. Please try again in {remaining + 1} minute(s).", "danger")
                return render_template('admin/login.html', form=form)
            else:
                user.locked_until = None
                user.failed_logins = 0
                db.session.commit()
                
        if user and user.is_active and user.check_password(form.password.data):
            user.failed_logins = 0
            user.locked_until = None
            db.session.commit()

            # Session Fixation Defense
            saved_csrf = session.get('csrf_token')
            session.clear()
            if saved_csrf:
                session['csrf_token'] = saved_csrf

            # Enforce MFA if enabled
            if user.mfa_enabled and user.mfa_secret:
                session['pre_auth_admin_id'] = user.id
                session['pre_auth_remember'] = form.remember_me.data
                session['pre_auth_next'] = request.args.get('next')
                session['pre_auth_time'] = time.time()
                log_security_event('PASSWORD_VERIFIED_MFA_REQUIRED', user=user)
                return redirect(url_for('admin.verify_mfa'))
            else:
                login_user(user, remember=form.remember_me.data)
                session['admin_user_id'] = user.id
                session['admin_token_version'] = user.token_version
                session['last_active'] = time.time()
                user.last_login = datetime.now(timezone.utc)
                db.session.commit()

                log_security_event('ADMIN_LOGIN_SUCCESS', user=user)
                flash(f"Welcome back, {user.username}! Admin Dashboard initialized.", "success")
                next_page = request.args.get('next')
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                return redirect(url_for('admin.dashboard'))
        else:
            if user:
                user.failed_logins = (user.failed_logins or 0) + 1
                if user.failed_logins >= 5:
                    user.locked_until = now + timedelta(minutes=15)
                    log_security_event('ACCOUNT_LOCKOUT_TRIGGERED', user=user, details="5 failed attempts -> 15 min lock", status='WARNING')
                    flash("Too many failed login attempts. This account has been locked for 15 minutes for defensive security.", "danger")
                else:
                    attempts_left = 5 - user.failed_logins
                    flash(f"Invalid username or password. {attempts_left} attempt(s) remaining before security lockout.", "danger")
                db.session.commit()
            else:
                flash("Invalid username or password.", "danger")
            log_security_event('LOGIN_FAILED', details=f"Failed login identifier: {identifier[:30]}", status='FAILED')

    return render_template('admin/login.html', form=form)

@admin_bp.route('/verify-mfa', methods=['GET', 'POST'])
def verify_mfa():
    user_id = session.get('pre_auth_admin_id')
    pre_auth_time = session.get('pre_auth_time')
    if not user_id or not pre_auth_time or (time.time() - pre_auth_time > 300):
        session.clear()
        flash("Your multi-factor authentication challenge has expired. Please sign in again.", "warning")
        return redirect(url_for('admin.login'))

    user = User.query.get(user_id)
    if not user or not user.is_active:
        session.clear()
        return redirect(url_for('admin.login'))

    form = MFAVerifyForm()
    if form.validate_on_submit():
        code = form.code.data.strip()
        if verify_totp_code(user.mfa_secret, code):
            remember = session.get('pre_auth_remember', False)
            next_url = session.get('pre_auth_next')
            saved_csrf = session.get('csrf_token')
            session.clear()
            if saved_csrf:
                session['csrf_token'] = saved_csrf

            login_user(user, remember=remember)
            session['admin_user_id'] = user.id
            session['admin_token_version'] = user.token_version
            session['last_active'] = time.time()
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()

            log_security_event('MFA_VERIFIED_LOGIN_SUCCESS', user=user)
            flash(f"MFA verified! Welcome back, {user.username}.", "success")
            if next_url and is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for('admin.dashboard'))
        else:
            log_security_event('MFA_VERIFY_FAILED', user=user, status='WARNING')
            flash("Invalid or expired 6-digit authentication code. Please try again.", "danger")

    return render_template('admin/verify_mfa.html', form=form, user=user)

@admin_bp.route('/setup-mfa', methods=['GET', 'POST'])
@admin_login_required
def setup_mfa():
    user = User.query.get(session.get('admin_user_id'))
    if not user:
        return redirect(url_for('admin.login'))

    secret = session.get('pending_mfa_secret')
    if not secret:
        secret = generate_totp_secret()
        session['pending_mfa_secret'] = secret

    otp_uri = get_totp_uri(secret, user.username)
    form = MFASetupForm()
    form.secret.data = secret

    if form.validate_on_submit():
        code = form.code.data.strip()
        if verify_totp_code(secret, code):
            user.mfa_secret = secret
            user.mfa_enabled = True
            db.session.commit()
            session.pop('pending_mfa_secret', None)
            log_security_event('MFA_SETUP_COMPLETED', user=user)
            flash("Multi-Factor Authentication enabled successfully! Your account is now secured.", "success")
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Verification code did not match. Please verify your device clock and re-enter the 6 digits.", "danger")

    return render_template('admin/setup_mfa.html', form=form, user=user, secret=secret, otp_uri=otp_uri)

@admin_bp.route('/logout')
def logout():
    user_id = session.get('admin_user_id')
    user = User.query.get(user_id) if user_id else None
    if user:
        log_security_event('ADMIN_LOGOUT', user=user)
    session.clear()
    logout_user()
    flash("You have been signed out from the Bitetech administration console.", "info")
    return redirect(url_for('admin.login'))

@admin_bp.route('/revoke-all-sessions', methods=['POST'])
@admin_login_required
def revoke_all_sessions():
    user = User.query.get(session.get('admin_user_id'))
    if user:
        user.token_version += 1
        db.session.commit()
        session['admin_token_version'] = user.token_version
        log_security_event('ALL_SESSIONS_REVOKED', user=user)
        flash("All other active admin sessions have been revoked.", "success")
    return redirect(url_for('admin.settings'))

# ----------------- ADMIN DASHBOARD -----------------
@admin_bp.route('/dashboard')
@admin_login_required
def dashboard():
    total_projects = Project.query.count()
    mini_projects_count = Project.query.filter_by(project_type='Mini').count()
    major_projects_count = Project.query.filter_by(project_type='Major').count()
    published_projects = Project.query.filter_by(is_published=True).count()
    unpublished_projects = total_projects - published_projects

    total_services = Service.query.count()
    total_courses = Course.query.count()
    available_courses = Course.query.filter_by(is_published=True).count()

    total_customers = User.query.filter(User.role.in_(['customer', 'student'])).count()

    total_project_enquiries = ProjectEnquiry.query.count()
    new_project_enquiries = ProjectEnquiry.query.filter_by(status='New').count()

    total_course_enquiries = CourseEnquiry.query.count()
    new_course_enquiries = CourseEnquiry.query.filter_by(status='New').count()

    total_service_enquiries = ServiceEnquiry.query.count()
    new_service_enquiries = ServiceEnquiry.query.filter_by(status='New').count()

    total_contact_msgs = ContactMessage.query.count()
    new_contact_msgs = ContactMessage.query.filter_by(status='New').count()

    total_enquiries = total_project_enquiries + total_course_enquiries + total_service_enquiries + total_contact_msgs
    new_enquiries = new_project_enquiries + new_course_enquiries + new_service_enquiries + new_contact_msgs

    # Recent items
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    recent_project_enquiries = ProjectEnquiry.query.order_by(ProjectEnquiry.created_at.desc()).limit(5).all()
    recent_course_enquiries = CourseEnquiry.query.order_by(CourseEnquiry.created_at.desc()).limit(5).all()
    recent_service_enquiries = ServiceEnquiry.query.order_by(ServiceEnquiry.created_at.desc()).limit(5).all()
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(6).all()

    return render_template(
        'admin/dashboard.html',
        total_projects=total_projects,
        mini_projects_count=mini_projects_count,
        major_projects_count=major_projects_count,
        published_projects=published_projects,
        unpublished_projects=unpublished_projects,
        total_services=total_services,
        total_courses=total_courses,
        available_courses=available_courses,
        total_customers=total_customers,
        total_enquiries=total_enquiries,
        new_enquiries=new_enquiries,
        recent_projects=recent_projects,
        recent_project_enquiries=recent_project_enquiries,
        recent_course_enquiries=recent_course_enquiries,
        recent_service_enquiries=recent_service_enquiries,
        recent_logs=recent_logs,
        incident_mode=get_incident_mode()
    )

# ----------------- PROJECT MANAGEMENT -----------------
@admin_bp.route('/projects')
@admin_login_required
def projects():
    page = request.args.get('page', 1, type=int)
    project_type = request.args.get('type', '').strip().capitalize()
    search = request.args.get('q', '').strip()

    query = Project.query
    if project_type in ('Mini', 'Major'):
        query = query.filter_by(project_type=project_type)
    if search:
        query = query.filter(Project.title.ilike(f"%{search}%"))

    projects_pagination = query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template(
        'admin/projects.html',
        projects=projects_pagination.items,
        pagination=projects_pagination,
        selected_type=project_type,
        search=search
    )

@admin_bp.route('/projects/new', methods=['GET', 'POST'])
@admin_login_required
def project_new():
    form = ProjectForm()
    categories = ProjectCategory.query.order_by(ProjectCategory.name).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        if Project.query.filter_by(slug=slug).first():
            flash("A project with this URL slug already exists. Please choose a unique slug.", "danger")
            return render_template('admin/project_form.html', form=form, title="Create Project")

        project = Project(
            title=form.title.data.strip(),
            slug=slug,
            category_id=form.category_id.data if form.category_id.data else None,
            project_type=form.project_type.data,
            starting_price=form.starting_price.data,
            price_range=form.price_range.data.strip(),
            short_description=form.short_description.data.strip(),
            full_description=form.full_description.data.strip(),
            problem_statement=form.problem_statement.data.strip() if form.problem_statement.data else None,
            features=form.features.data.strip() if form.features.data else None,
            deliverables=form.deliverables.data.strip() if form.deliverables.data else None,
            tech_stack=form.tech_stack.data.strip(),
            source_code_included=form.source_code_included.data,
            availability_status=form.availability_status.data,
            is_demo=form.is_demo.data,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data,
            image_url=form.image_url.data.strip() if form.image_url.data else None,
            demo_link=form.demo_link.data.strip() if form.demo_link.data else None
        )
        db.session.add(project)
        db.session.commit()

        log_security_event('PROJECT_CREATED', user=current_user, target_type='Project', target_id=project.id, details=f"Created {project.title}")
        flash(f"Project '{project.title}' created successfully!", "success")
        return redirect(url_for('admin.projects'))

    return render_template('admin/project_form.html', form=form, title="Create Project")

@admin_bp.route('/projects/<int:id>/edit', methods=['GET', 'POST'])
@admin_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def project_edit(id=None, project_id=None):
    pid = id or project_id
    project = Project.query.get_or_404(pid)
    form = ProjectForm(obj=project)
    categories = ProjectCategory.query.order_by(ProjectCategory.name).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        existing = Project.query.filter(Project.slug == slug, Project.id != project.id).first()
        if existing:
            flash("A project with this URL slug already exists. Please choose a unique slug.", "danger")
            return render_template('admin/project_form.html', form=form, title=f"Edit: {project.title}", project=project)

        form.populate_obj(project)
        project.slug = slug
        db.session.commit()

        log_security_event('PROJECT_UPDATED', user=current_user, target_type='Project', target_id=project.id)
        flash(f"Project '{project.title}' updated successfully!", "success")
        return redirect(url_for('admin.projects'))

    return render_template('admin/project_form.html', form=form, title=f"Edit: {project.title}", project=project)

@admin_bp.route('/projects/<int:id>/toggle-publish', methods=['POST'])
@admin_bp.route('/projects/<int:project_id>/toggle-publish', methods=['POST'])
@admin_login_required
def project_toggle_publish(id=None, project_id=None):
    pid = id or project_id
    project = Project.query.get_or_404(pid)
    project.is_published = not project.is_published
    db.session.commit()

    log_security_event('PROJECT_TOGGLED', user=current_user, target_type='Project', target_id=project.id, details=f"Published={project.is_published}")
    flash(f"Project '{project.title}' status updated.", "info")
    return redirect(url_for('admin.projects'))

@admin_bp.route('/projects/<int:id>/delete', methods=['POST'])
@admin_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@admin_login_required
def project_delete(id=None, project_id=None):
    pid = id or project_id
    project = Project.query.get_or_404(pid)
    title = project.title
    db.session.delete(project)
    db.session.commit()

    log_security_event('PROJECT_DELETED', user=current_user, target_type='Project', target_id=pid, details=f"Deleted {title}")
    flash(f"Project '{title}' has been removed.", "info")
    return redirect(url_for('admin.projects'))

# ----------------- SERVICE & PRICING MANAGEMENT -----------------
@admin_bp.route('/services')
@admin_login_required
def services():
    services_list = Service.query.order_by(Service.price_integer.asc()).all()
    return render_template('admin/services.html', services=services_list)

@admin_bp.route('/services/new', methods=['GET', 'POST'])
@admin_login_required
def service_new():
    form = ServiceForm()
    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        if Service.query.filter_by(slug=slug).first():
            flash("A service with this URL slug already exists. Please use a unique slug.", "danger")
            return render_template('admin/service_form.html', form=form, title="Create Service Package")

        service = Service(
            title=form.title.data.strip(),
            slug=slug,
            starting_price=form.starting_price.data.strip(),
            price_integer=form.price_integer.data,
            timeline=form.timeline.data.strip(),
            short_description=form.short_description.data.strip(),
            full_description=form.full_description.data.strip(),
            features=form.features.data.strip() if form.features.data else None,
            deliverables=form.deliverables.data.strip() if form.deliverables.data else None,
            project_requirements=form.project_requirements.data.strip() if form.project_requirements.data else None,
            hosting_duration=form.hosting_duration.data.strip() if form.hosting_duration.data else None,
            domain_included=form.domain_included.data.strip() if form.domain_included.data else None,
            renewal_cost=form.renewal_cost.data.strip() if form.renewal_cost.data else None,
            additional_charges=form.additional_charges.data.strip() if form.additional_charges.data else None,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data
        )
        db.session.add(service)
        db.session.commit()

        log_security_event('SERVICE_CREATED', user=current_user, target_type='Service', target_id=service.id, details=f"Created {service.title}")
        flash(f"Service package '{service.title}' created successfully!", "success")
        return redirect(url_for('admin.services'))

    return render_template('admin/service_form.html', form=form, title="Create Service Package")

@admin_bp.route('/services/<int:id>/edit', methods=['GET', 'POST'])
@admin_bp.route('/services/<int:service_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def service_edit(id=None, service_id=None):
    sid = id or service_id
    service = Service.query.get_or_404(sid)
    form = ServiceForm(obj=service)

    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        existing = Service.query.filter(Service.slug == slug, Service.id != service.id).first()
        if existing:
            flash("A service with this URL slug already exists. Please choose a unique slug.", "danger")
            return render_template('admin/service_form.html', form=form, title=f"Edit: {service.title}", service=service)

        form.populate_obj(service)
        service.slug = slug
        db.session.commit()

        log_security_event('SERVICE_UPDATED', user=current_user, target_type='Service', target_id=service.id)
        flash(f"Service package '{service.title}' updated successfully!", "success")
        return redirect(url_for('admin.services'))

    return render_template('admin/service_form.html', form=form, title=f"Edit: {service.title}", service=service)

@admin_bp.route('/services/<int:id>/delete', methods=['POST'])
@admin_bp.route('/services/<int:service_id>/delete', methods=['POST'])
@admin_login_required
def service_delete(id=None, service_id=None):
    sid = id or service_id
    service = Service.query.get_or_404(sid)
    title = service.title
    db.session.delete(service)
    db.session.commit()

    log_security_event('SERVICE_DELETED', user=current_user, target_type='Service', target_id=sid, details=f"Deleted {title}")
    flash(f"Service '{title}' has been removed.", "info")
    return redirect(url_for('admin.services'))

# ----------------- COURSE MANAGEMENT -----------------
@admin_bp.route('/courses')
@admin_login_required
def courses():
    courses_list = Course.query.order_by(Course.fee_integer.asc()).all()
    return render_template('admin/courses.html', courses=courses_list)

@admin_bp.route('/courses/new', methods=['GET', 'POST'])
@admin_login_required
def course_new():
    form = CourseForm()
    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        if Course.query.filter_by(slug=slug).first():
            flash("A course with this URL slug already exists.", "danger")
            return render_template('admin/course_form.html', form=form, title="Create Course")

        course = Course(
            title=form.title.data.strip(),
            slug=slug,
            level=form.level.data,
            duration=form.duration.data.strip(),
            price=form.price.data.strip(),
            fee_integer=form.fee_integer.data,
            delivery_mode=form.delivery_mode.data,
            class_schedule=form.class_schedule.data.strip(),
            teaching_format=form.teaching_format.data.strip(),
            status=form.status.data,
            short_description=form.short_description.data.strip(),
            syllabus=form.syllabus.data.strip(),
            outcomes=form.outcomes.data.strip() if form.outcomes.data else None,
            prerequisites=form.prerequisites.data.strip() if form.prerequisites.data else None,
            badge_text=form.badge_text.data.strip() if form.badge_text.data else None,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data
        )
        db.session.add(course)
        db.session.commit()

        log_security_event('COURSE_CREATED', user=current_user, target_type='Course', target_id=course.id, details=f"Created {course.title}")
        flash(f"Course '{course.title}' created successfully!", "success")
        return redirect(url_for('admin.courses'))

    return render_template('admin/course_form.html', form=form, title="Create Course")

@admin_bp.route('/courses/<int:id>/edit', methods=['GET', 'POST'])
@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def course_edit(id=None, course_id=None):
    cid = id or course_id
    course = Course.query.get_or_404(cid)
    form = CourseForm(obj=course)

    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        existing = Course.query.filter(Course.slug == slug, Course.id != course.id).first()
        if existing:
            flash("A course with this URL slug already exists.", "danger")
            return render_template('admin/course_form.html', form=form, title=f"Edit: {course.title}", course=course)

        form.populate_obj(course)
        course.slug = slug
        db.session.commit()

        log_security_event('COURSE_UPDATED', user=current_user, target_type='Course', target_id=course.id)
        flash(f"Course '{course.title}' updated successfully!", "success")
        return redirect(url_for('admin.courses'))

    return render_template('admin/course_form.html', form=form, title=f"Edit: {course.title}", course=course)

@admin_bp.route('/courses/<int:id>/delete', methods=['POST'])
@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@admin_login_required
def course_delete(id=None, course_id=None):
    cid = id or course_id
    course = Course.query.get_or_404(cid)
    title = course.title
    db.session.delete(course)
    db.session.commit()

    log_security_event('COURSE_DELETED', user=current_user, target_type='Course', target_id=cid, details=f"Deleted {title}")
    flash(f"Course '{title}' has been removed.", "info")
    return redirect(url_for('admin.courses'))

# ----------------- CUSTOMER MANAGEMENT -----------------
@admin_bp.route('/customers')
@admin_login_required
def customers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()

    query = User.query.filter(User.role.in_(['customer', 'student']))
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (User.username.ilike(pattern)) |
            (User.email.ilike(pattern)) |
            (User.full_name.ilike(pattern))
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template(
        'admin/customers.html',
        customers=pagination.items,
        pagination=pagination,
        search=search
    )

@admin_bp.route('/customers/<int:user_id>/toggle-status', methods=['POST'])
@admin_login_required
def customer_toggle_status(user_id):
    customer = User.query.get_or_404(user_id)
    customer.is_active = not customer.is_active
    db.session.commit()

    log_security_event('CUSTOMER_STATUS_TOGGLED', user=current_user, target_type='User', target_id=customer.id, details=f"Active={customer.is_active}")
    flash(f"Customer '{customer.username}' status set to {'Active' if customer.is_active else 'Deactivated'}.", "info")
    return redirect(url_for('admin.customers'))

# ----------------- ENQUIRIES & WORKFLOWS -----------------
@admin_bp.route('/enquiries')
@admin_login_required
def enquiries():
    enquiry_type = request.args.get('type', 'all')
    status_filter = request.args.get('status', 'all')

    p_query = ProjectEnquiry.query
    c_query = CourseEnquiry.query
    s_query = ServiceEnquiry.query
    m_query = ContactMessage.query

    if status_filter != 'all':
        p_query = p_query.filter_by(status=status_filter)
        c_query = c_query.filter_by(status=status_filter)
        s_query = s_query.filter_by(status=status_filter)
        m_query = m_query.filter_by(status=status_filter)

    project_enquiries = p_query.order_by(ProjectEnquiry.created_at.desc()).all()
    course_enquiries = c_query.order_by(CourseEnquiry.created_at.desc()).all()
    service_enquiries = s_query.order_by(ServiceEnquiry.created_at.desc()).all()
    contact_messages = m_query.order_by(ContactMessage.created_at.desc()).all()

    return render_template(
        'admin/enquiries.html',
        enquiry_type=enquiry_type,
        status_filter=status_filter,
        project_enquiries=project_enquiries,
        course_enquiries=course_enquiries,
        service_enquiries=service_enquiries,
        contact_messages=contact_messages
    )

@admin_bp.route('/enquiries/project/<int:enquiry_id>/status', methods=['POST'])
@admin_login_required
def project_enquiry_status(enquiry_id):
    enquiry = ProjectEnquiry.query.get_or_404(enquiry_id)
    new_status = request.form.get('status', 'New')
    notes = request.form.get('admin_notes', '').strip()
    response = request.form.get('company_response', '').strip()

    if new_status in ('New', 'Contacted', 'In Progress', 'Completed', 'Rejected'):
        enquiry.status = new_status
        if notes:
            enquiry.admin_notes = notes
        if response:
            enquiry.company_response = response
        db.session.commit()
        log_security_event('ENQUIRY_STATUS_UPDATED', user=current_user, target_type='ProjectEnquiry', target_id=enquiry.id, details=f"Status={new_status}")
        flash(f"Project enquiry #{enquiry.id} updated to '{new_status}'.", "success")

    return redirect(url_for('admin.enquiries', type='projects'))

@admin_bp.route('/enquiries/course/<int:enquiry_id>/status', methods=['POST'])
@admin_login_required
def course_enquiry_status(enquiry_id):
    enquiry = CourseEnquiry.query.get_or_404(enquiry_id)
    new_status = request.form.get('status', 'New')
    notes = request.form.get('admin_notes', '').strip()
    response = request.form.get('company_response', '').strip()

    if new_status in ('New', 'Contacted', 'In Progress', 'Completed', 'Rejected'):
        enquiry.status = new_status
        if notes:
            enquiry.admin_notes = notes
        if response:
            enquiry.company_response = response
        db.session.commit()
        log_security_event('ENQUIRY_STATUS_UPDATED', user=current_user, target_type='CourseEnquiry', target_id=enquiry.id, details=f"Status={new_status}")
        flash(f"Course registration enquiry #{enquiry.id} updated to '{new_status}'.", "success")

    return redirect(url_for('admin.enquiries', type='courses'))

@admin_bp.route('/enquiries/service/<int:enquiry_id>/status', methods=['POST'])
@admin_login_required
def service_enquiry_status(enquiry_id):
    enquiry = ServiceEnquiry.query.get_or_404(enquiry_id)
    new_status = request.form.get('status', 'New')
    notes = request.form.get('admin_notes', '').strip()
    response = request.form.get('company_response', '').strip()

    if new_status in ('New', 'Contacted', 'In Progress', 'Completed', 'Rejected'):
        enquiry.status = new_status
        if notes:
            enquiry.admin_notes = notes
        if response:
            enquiry.company_response = response
        db.session.commit()
        log_security_event('ENQUIRY_STATUS_UPDATED', user=current_user, target_type='ServiceEnquiry', target_id=enquiry.id, details=f"Status={new_status}")
        flash(f"Service quotation enquiry #{enquiry.id} updated to '{new_status}'.", "success")

    return redirect(url_for('admin.enquiries', type='services'))

@admin_bp.route('/enquiries/contact/<int:msg_id>/status', methods=['POST'])
@admin_login_required
def contact_message_status(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    new_status = request.form.get('status', 'New')
    notes = request.form.get('admin_notes', '').strip()

    if new_status in ('New', 'Contacted', 'In Progress', 'Completed', 'Rejected'):
        msg.status = new_status
        if notes:
            msg.admin_notes = notes
        db.session.commit()
        log_security_event('ENQUIRY_STATUS_UPDATED', user=current_user, target_type='ContactMessage', target_id=msg.id, details=f"Status={new_status}")
        flash(f"Contact message #{msg.id} updated to '{new_status}'.", "success")

    return redirect(url_for('admin.enquiries', type='contacts'))

@admin_bp.route('/enquiries/project/<int:enquiry_id>/delete', methods=['POST'])
@admin_login_required
def project_enquiry_delete(enquiry_id):
    enquiry = ProjectEnquiry.query.get_or_404(enquiry_id)
    client_name = enquiry.client_name
    db.session.delete(enquiry)
    db.session.commit()
    log_security_event('PROJECT_ENQUIRY_DELETED', user=current_user, target_type='ProjectEnquiry', target_id=enquiry_id, details=f"Deleted enquiry from {client_name}")
    flash(f"Project enquiry #{enquiry_id} from '{client_name}' has been deleted.", "info")
    return redirect(url_for('admin.enquiries', type='projects'))

@admin_bp.route('/enquiries/course/<int:enquiry_id>/delete', methods=['POST'])
@admin_login_required
def course_enquiry_delete(enquiry_id):
    enquiry = CourseEnquiry.query.get_or_404(enquiry_id)
    student_name = enquiry.student_name
    db.session.delete(enquiry)
    db.session.commit()
    log_security_event('COURSE_ENQUIRY_DELETED', user=current_user, target_type='CourseEnquiry', target_id=enquiry_id, details=f"Deleted registration enquiry from {student_name}")
    flash(f"Course registration enquiry #{enquiry_id} from '{student_name}' has been deleted.", "info")
    return redirect(url_for('admin.enquiries', type='courses'))

@admin_bp.route('/enquiries/service/<int:enquiry_id>/delete', methods=['POST'])
@admin_login_required
def service_enquiry_delete(enquiry_id):
    enquiry = ServiceEnquiry.query.get_or_404(enquiry_id)
    client_name = enquiry.client_name
    db.session.delete(enquiry)
    db.session.commit()
    log_security_event('SERVICE_ENQUIRY_DELETED', user=current_user, target_type='ServiceEnquiry', target_id=enquiry_id, details=f"Deleted service enquiry from {client_name}")
    flash(f"Service quotation enquiry #{enquiry_id} from '{client_name}' has been deleted.", "info")
    return redirect(url_for('admin.enquiries', type='services'))

@admin_bp.route('/enquiries/contact/<int:msg_id>/delete', methods=['POST'])
@admin_login_required
def contact_message_delete(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    name = msg.name
    db.session.delete(msg)
    db.session.commit()
    log_security_event('CONTACT_MESSAGE_DELETED', user=current_user, target_type='ContactMessage', target_id=msg_id, details=f"Deleted contact message from {name}")
    flash(f"Contact message #{msg_id} from '{name}' has been deleted.", "info")
    return redirect(url_for('admin.enquiries', type='contacts'))

@admin_bp.route('/enquiries/export')
@admin_login_required
def enquiries_export():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Record Type', 'ID', 'Name / Student', 'Email', 'Phone',
        'Item Title / Scope', 'Budget / Fee', 'Requirements / Message',
        'Status', 'Admin Notes', 'Date Submitted (UTC)'
    ])

    for pe in ProjectEnquiry.query.order_by(ProjectEnquiry.created_at.desc()).all():
        writer.writerow([
            'Project Enquiry', pe.id, pe.client_name, pe.client_email, pe.client_phone,
            pe.project.title if pe.project else pe.project_type, pe.budget_range,
            pe.requirements, pe.status, pe.admin_notes or '', pe.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    for se in ServiceEnquiry.query.order_by(ServiceEnquiry.created_at.desc()).all():
        writer.writerow([
            'Service Enquiry', se.id, se.client_name, se.client_email, se.client_phone,
            se.service.title if se.service else se.project_title, se.budget_range,
            se.project_requirements, se.status, se.admin_notes or '', se.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    for ce in CourseEnquiry.query.order_by(CourseEnquiry.created_at.desc()).all():
        writer.writerow([
            'Course Registration', ce.id, ce.student_name, ce.student_email, ce.student_phone,
            ce.course.title if ce.course else 'General Course', ce.preferred_batch,
            ce.message, ce.status, ce.admin_notes or '', ce.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    for cm in ContactMessage.query.order_by(ContactMessage.created_at.desc()).all():
        writer.writerow([
            'Contact Desk', cm.id, cm.name, cm.email, cm.phone,
            cm.subject, cm.budget, cm.message, cm.status, cm.admin_notes or '', cm.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    log_security_event('CSV_EXPORT_DOWNLOADED', user=current_user)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=bitetech_enquiries_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

# ----------------- CATEGORY MANAGEMENT -----------------
@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_login_required
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        if ProjectCategory.query.filter_by(slug=slug).first():
            flash("Category with this URL slug already exists.", "danger")
        else:
            cat = ProjectCategory(
                name=form.name.data.strip(),
                slug=slug,
                description=form.description.data.strip() if form.description.data else None
            )
            db.session.add(cat)
            db.session.commit()
            flash(f"Category '{cat.name}' created.", "success")
            return redirect(url_for('admin.categories'))

    all_categories = ProjectCategory.query.order_by(ProjectCategory.name).all()
    return render_template('admin/categories.html', form=form, categories=all_categories)

@admin_bp.route('/categories/<int:id>/delete', methods=['POST'])
@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@admin_login_required
def category_delete(id=None, cat_id=None):
    cid = id or cat_id
    cat = ProjectCategory.query.get_or_404(cid)
    name = cat.name
    db.session.delete(cat)
    db.session.commit()
    flash(f"Category '{name}' deleted.", "info")
    return redirect(url_for('admin.categories'))

# ----------------- PORTFOLIO MANAGEMENT -----------------
@admin_bp.route('/portfolio')
@admin_login_required
def portfolio():
    items = PortfolioItem.query.order_by(PortfolioItem.created_at.desc()).all()
    return render_template('admin/portfolio.html', items=items)

@admin_bp.route('/portfolio/new', methods=['GET', 'POST'])
@admin_login_required
def portfolio_new():
    form = PortfolioForm()
    if form.validate_on_submit():
        item = PortfolioItem(
            title=form.title.data.strip(),
            category=form.category.data.strip(),
            description=form.description.data.strip(),
            client_type=form.client_type.data.strip() if form.client_type.data else 'Engineering Demonstration',
            features=form.features.data.strip() if form.features.data else None,
            technologies=form.technologies.data.strip(),
            image_url=form.image_url.data.strip() if form.image_url.data else None,
            live_url=form.live_url.data.strip() if form.live_url.data else None,
            is_published=form.is_published.data
        )
        db.session.add(item)
        db.session.commit()
        flash(f"Portfolio item '{item.title}' added successfully.", "success")
        return redirect(url_for('admin.portfolio'))

    return render_template('admin/portfolio_form.html', form=form, title="New Portfolio Item")

@admin_bp.route('/portfolio/<int:id>/edit', methods=['GET', 'POST'])
@admin_bp.route('/portfolio/<int:item_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def portfolio_edit(id=None, item_id=None):
    iid = id or item_id
    item = PortfolioItem.query.get_or_404(iid)
    form = PortfolioForm(obj=item)
    if form.validate_on_submit():
        form.populate_obj(item)
        db.session.commit()
        flash(f"Portfolio item '{item.title}' updated successfully.", "success")
        return redirect(url_for('admin.portfolio'))

    return render_template('admin/portfolio_form.html', form=form, title=f"Edit: {item.title}", item=item)

@admin_bp.route('/portfolio/<int:id>/delete', methods=['POST'])
@admin_bp.route('/portfolio/<int:item_id>/delete', methods=['POST'])
@admin_login_required
def portfolio_delete(id=None, item_id=None):
    iid = id or item_id
    item = PortfolioItem.query.get_or_404(iid)
    title = item.title
    db.session.delete(item)
    db.session.commit()
    flash(f"Portfolio item '{title}' deleted.", "info")
    return redirect(url_for('admin.portfolio'))

# ----------------- FAQ MANAGEMENT -----------------
@admin_bp.route('/faqs')
@admin_login_required
def faqs():
    faq_list = FAQ.query.order_by(FAQ.display_order.asc(), FAQ.id.asc()).all()
    return render_template('admin/faqs.html', faqs=faq_list)

@admin_bp.route('/faqs/new', methods=['GET', 'POST'])
@admin_login_required
def faq_new():
    form = FAQForm()
    if form.validate_on_submit():
        faq = FAQ(
            question=form.question.data.strip(),
            answer=form.answer.data.strip(),
            category=form.category.data,
            display_order=form.display_order.data or 0,
            is_published=form.is_published.data
        )
        db.session.add(faq)
        db.session.commit()
        flash("FAQ created successfully.", "success")
        return redirect(url_for('admin.faqs'))

    return render_template('admin/faq_form.html', form=form, title="Create FAQ")

@admin_bp.route('/faqs/<int:id>/edit', methods=['GET', 'POST'])
@admin_bp.route('/faqs/<int:faq_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def faq_edit(id=None, faq_id=None):
    fid = id or faq_id
    faq = FAQ.query.get_or_404(fid)
    form = FAQForm(obj=faq)
    if form.validate_on_submit():
        form.populate_obj(faq)
        db.session.commit()
        flash("FAQ updated successfully.", "success")
        return redirect(url_for('admin.faqs'))

    return render_template('admin/faq_form.html', form=form, title=f"Edit FAQ #{faq.id}", faq=faq)

@admin_bp.route('/faqs/<int:id>/delete', methods=['POST'])
@admin_bp.route('/faqs/<int:faq_id>/delete', methods=['POST'])
@admin_login_required
def faq_delete(id=None, faq_id=None):
    fid = id or faq_id
    faq = FAQ.query.get_or_404(fid)
    db.session.delete(faq)
    db.session.commit()
    flash("FAQ deleted successfully.", "info")
    return redirect(url_for('admin.faqs'))

# ----------------- SITE SETTINGS & POLICIES -----------------
@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_login_required
def settings():
    form = SiteSettingsForm()
    keys = [
        'company_name', 'company_email', 'company_phone', 'whatsapp_number',
        'starting_price', 'hero_headline', 'hero_subheadline',
        'about_text', 'mission_text', 'vision_text',
        'privacy_policy', 'terms_conditions', 'refund_policy',
        'project_delivery_policy', 'hosting_renewal_policy', 'incident_mode'
    ]

    if request.method == 'GET':
        for k in keys:
            if hasattr(form, k):
                field = getattr(form, k)
                val = SiteSetting.get_setting(k, '')
                field.data = val

    if form.validate_on_submit():
        for k in keys:
            if hasattr(form, k):
                val = getattr(form, k).data
                if val is not None:
                    SiteSetting.set_setting(k, str(val).strip())

        log_security_event('SETTINGS_UPDATED', user=current_user)
        flash("Company settings, hero text, and policies updated successfully!", "success")
        return redirect(url_for('admin.settings'))

    user = User.query.get(session.get('admin_user_id'))
    return render_template('admin/settings.html', form=form, user=user)

# ----------------- SECURITY AUDIT LOGS -----------------
@admin_bp.route('/audit-logs')
@admin_login_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()

    query = AuditLog.query
    if action_filter:
        query = query.filter_by(action=action_filter)

    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template(
        'admin/audit_logs.html',
        logs=pagination.items,
        pagination=pagination,
        action_filter=action_filter
    )
