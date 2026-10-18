from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db

def utc_now():
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default='customer', nullable=False, index=True)  # 'admin', 'superadmin', 'customer', 'student'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_logins = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    mfa_secret = db.Column(db.String(64), nullable=True)
    mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    token_version = db.Column(db.Integer, default=1, nullable=False)
    password_changed_at = db.Column(db.DateTime, default=utc_now)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    project_enquiries = db.relationship('ProjectEnquiry', back_populates='user', cascade='all, delete-orphan')
    course_enquiries = db.relationship('CourseEnquiry', back_populates='user', cascade='all, delete-orphan')
    service_enquiries = db.relationship('ServiceEnquiry', back_populates='user', cascade='all, delete-orphan')
    contact_messages = db.relationship('ContactMessage', back_populates='user')
    orders = db.relationship('ProjectOrder', back_populates='user', cascade='all, delete-orphan')
    reset_tokens = db.relationship('PasswordResetToken', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='scrypt')
        self.password_changed_at = utc_now()
        self.token_version = (self.token_version or 1) + 1

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role in ('admin', 'superadmin')

    @property
    def is_customer(self):
        return self.role in ('customer', 'student')

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'

# Backward compatibility alias for existing admin references
AdminUser = User

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token_hash = db.Column(db.String(128), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    user = db.relationship('User', back_populates='reset_tokens')

    def is_valid(self):
        now = utc_now()
        token_exp = self.expires_at
        if token_exp.tzinfo is None:
            token_exp = token_exp.replace(tzinfo=timezone.utc)
        return (not self.used) and (now < token_exp)

class ProjectCategory(db.Model):
    __tablename__ = 'project_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    projects = db.relationship('Project', back_populates='category', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ProjectCategory {self.name}>'

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('project_categories.id'), nullable=True)
    project_type = db.Column(db.String(50), default='Mini', nullable=False, index=True)  # 'Mini', 'Major'
    short_description = db.Column(db.String(350), nullable=False)
    full_description = db.Column(db.Text, nullable=False)
    problem_statement = db.Column(db.Text, nullable=True)
    features = db.Column(db.Text, nullable=True)  # Newline-separated list of highlights
    deliverables = db.Column(db.Text, nullable=True)  # Newline-separated list of deliverables
    tech_stack = db.Column(db.String(255), nullable=False, default='Python, Flask, MySQL')
    starting_price = db.Column(db.Integer, default=599, nullable=False)  # 599 for mini, 1000 for major
    price_range = db.Column(db.String(100), default='From ₹599')
    source_code_included = db.Column(db.Boolean, default=True, nullable=False)
    availability_status = db.Column(db.String(50), default='Available', nullable=False)  # 'Available', 'Custom Order', 'Archived'
    is_demo = db.Column(db.Boolean, default=True, nullable=False)  # Labels demo/reference projects
    is_published = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    demo_link = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    category = db.relationship('ProjectCategory', back_populates='projects')
    enquiries = db.relationship('ProjectEnquiry', back_populates='project', cascade='all, delete-orphan')

    def feature_list(self):
        if not self.features:
            return []
        return [f.strip() for f in self.features.splitlines() if f.strip()]

    def deliverable_list(self):
        if not self.deliverables:
            return [
                "Full commented Python source code",
                "Database setup script (WAMP MySQL & SQLite)",
                "Step-by-step setup guide and execution instructions",
                "Project architecture overview & viva assistance"
            ]
        return [d.strip() for d in self.deliverables.splitlines() if d.strip()]

    def tech_list(self):
        if not self.tech_stack:
            return []
        return [t.strip() for t in self.tech_stack.split(',') if t.strip()]

    def __repr__(self):
        return f'<Project {self.title}>'

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    short_description = db.Column(db.String(350), nullable=False)
    full_description = db.Column(db.Text, nullable=False)
    starting_price = db.Column(db.String(100), default='₹5,000', nullable=False)
    price_integer = db.Column(db.Integer, default=5000, nullable=False)
    timeline = db.Column(db.String(100), default='5-7 Working Days', nullable=False)
    features = db.Column(db.Text, nullable=True)  # Newline-separated
    deliverables = db.Column(db.Text, nullable=True)  # Newline-separated
    project_requirements = db.Column(db.Text, nullable=True)
    hosting_duration = db.Column(db.String(200), default='Configurable (e.g. 1 Year or Not Included)', nullable=True)
    domain_included = db.Column(db.String(200), default='Optional / As configured by company', nullable=True)
    renewal_cost = db.Column(db.String(200), default='Billed annually as per selected hosting provider', nullable=True)
    additional_charges = db.Column(db.String(255), default='Payment gateway setup, extra pages, and premium plugins charged separately', nullable=True)
    is_published = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    enquiries = db.relationship('ServiceEnquiry', back_populates='service', cascade='all, delete-orphan')

    def feature_list(self):
        if not self.features:
            return []
        return [f.strip() for f in self.features.splitlines() if f.strip()]

    def deliverable_list(self):
        if not self.deliverables:
            return []
        return [d.strip() for d in self.deliverables.splitlines() if d.strip()]

    def __repr__(self):
        return f'<Service {self.title}>'

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    level = db.Column(db.String(50), default='Beginner', nullable=False)
    duration = db.Column(db.String(100), default='4 Weeks', nullable=False)
    price = db.Column(db.String(100), default='₹899', nullable=False)
    fee_integer = db.Column(db.Integer, default=899, nullable=False)
    short_description = db.Column(db.String(350), nullable=False)
    syllabus = db.Column(db.Text, nullable=False)  # Multi-line formatted modules
    outcomes = db.Column(db.Text, nullable=True)
    prerequisites = db.Column(db.String(255), default='Basic computer knowledge; no prior coding experience needed.')
    delivery_mode = db.Column(db.String(50), default='Online Live Mentoring', nullable=False)
    class_schedule = db.Column(db.String(150), default='Weekend & Evening Batches Available', nullable=False)
    teaching_format = db.Column(db.String(150), default='Live Screen-Share, Code Review, and Hands-on Tasks', nullable=False)
    status = db.Column(db.String(50), default='Enrolling', nullable=False)
    badge_text = db.Column(db.String(50), nullable=True)
    is_published = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    enquiries = db.relationship('CourseEnquiry', back_populates='course', cascade='all, delete-orphan')

    def syllabus_modules(self):
        """Parse lines formatted as Module X: Title | Detail into list of dicts"""
        if not self.syllabus:
            return []
        lines = [line.strip() for line in self.syllabus.splitlines() if line.strip()]
        modules = []
        for line in lines:
            if '|' in line:
                title, desc = line.split('|', 1)
                modules.append({'title': title.strip(), 'detail': desc.strip()})
            else:
                modules.append({'title': line, 'detail': ''})
        return modules

    def outcomes_list(self):
        if not self.outcomes:
            return []
        return [o.strip() for o in self.outcomes.splitlines() if o.strip()]

    def __repr__(self):
        return f'<Course {self.title}>'

class PortfolioItem(db.Model):
    __tablename__ = 'portfolio_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    client_type = db.Column(db.String(150), default='Academic / Engineering Demonstration')
    features = db.Column(db.Text, nullable=True)
    technologies = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    live_url = db.Column(db.String(500), nullable=True)
    is_published = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def tech_list(self):
        if not self.technologies:
            return []
        return [t.strip() for t in self.technologies.split(',') if t.strip()]

    def feature_list(self):
        if not self.features:
            return []
        return [f.strip() for f in self.features.splitlines() if f.strip()]

    def __repr__(self):
        return f'<PortfolioItem {self.title}>'

class ProjectEnquiry(db.Model):
    __tablename__ = 'project_enquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    client_name = db.Column(db.String(120), nullable=False)
    client_email = db.Column(db.String(120), nullable=False)
    client_phone = db.Column(db.String(30), nullable=False)
    project_type = db.Column(db.String(100), nullable=True)
    budget_range = db.Column(db.String(100), default='₹599 - ₹1,500')
    requirements = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='New', nullable=False, index=True)  # New, Contacted, In Progress, Completed, Rejected
    admin_notes = db.Column(db.Text, nullable=True)
    company_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, index=True)

    project = db.relationship('Project', back_populates='enquiries')
    user = db.relationship('User', back_populates='project_enquiries')

    def __repr__(self):
        return f'<ProjectEnquiry {self.client_name} - {self.status}>'

class CourseEnquiry(db.Model):
    __tablename__ = 'course_enquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    student_name = db.Column(db.String(120), nullable=False)
    student_email = db.Column(db.String(120), nullable=False)
    student_phone = db.Column(db.String(30), nullable=False)
    preferred_batch = db.Column(db.String(50), default='Weekend')
    learning_mode = db.Column(db.String(50), default='Online Live')
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='New', nullable=False, index=True)
    admin_notes = db.Column(db.Text, nullable=True)
    company_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, index=True)

    course = db.relationship('Course', back_populates='enquiries')
    user = db.relationship('User', back_populates='course_enquiries')

    def __repr__(self):
        return f'<CourseEnquiry {self.student_name} - {self.status}>'

class ServiceEnquiry(db.Model):
    __tablename__ = 'service_enquiries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='SET NULL'), nullable=True)
    client_name = db.Column(db.String(120), nullable=False)
    client_email = db.Column(db.String(120), nullable=False)
    client_phone = db.Column(db.String(30), nullable=False)
    project_title = db.Column(db.String(200), nullable=False)
    budget_range = db.Column(db.String(100), default='₹5,000 - ₹10,000')
    project_requirements = db.Column(db.Text, nullable=False)
    target_timeline = db.Column(db.String(100), default='1-2 Weeks')
    status = db.Column(db.String(30), default='New', nullable=False, index=True)
    admin_notes = db.Column(db.Text, nullable=True)
    company_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, index=True)

    service = db.relationship('Service', back_populates='enquiries')
    user = db.relationship('User', back_populates='service_enquiries')

    def __repr__(self):
        return f'<ServiceEnquiry {self.client_name} - {self.status}>'

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    service = db.Column(db.String(100), default='Python Project Development')
    budget = db.Column(db.String(100), default='₹599 - ₹2,000')
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='New', nullable=False, index=True)
    admin_notes = db.Column(db.Text, nullable=True)
    company_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, index=True)

    user = db.relationship('User', back_populates='contact_messages')

    def __repr__(self):
        return f'<ContactMessage {self.name} - {self.subject}>'

class ProjectOrder(db.Model):
    __tablename__ = 'project_orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    order_type = db.Column(db.String(50), nullable=False)  # 'Project', 'Service', 'Course'
    item_id = db.Column(db.Integer, nullable=True)
    item_title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.String(100), default='₹599')
    requirements = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Pending Review', nullable=False, index=True)  # Pending Review, Quoted, In Progress, Delivered, Cancelled
    admin_notes = db.Column(db.Text, nullable=True)
    company_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, index=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    user = db.relationship('User', back_populates='orders')

    def __repr__(self):
        return f'<ProjectOrder #{self.id} {self.item_title} [{self.status}]>'

class FAQ(db.Model):
    __tablename__ = 'faqs'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(300), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default='General')  # Projects, Classes, Services & Hosting, Payments & Support, General
    display_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f'<FAQ {self.question[:30]}>'

class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    @classmethod
    def get_setting(cls, key, default=''):
        item = cls.query.filter_by(key=key).first()
        return item.value if item and item.value is not None else default

    @classmethod
    def set_setting(cls, key, value, description=None):
        item = cls.query.filter_by(key=key).first()
        if not item:
            item = cls(key=key, value=value, description=description)
            db.session.add(item)
        else:
            item.value = value
            if description:
                item.description = description
        db.session.commit()
        return item

    def __repr__(self):
        return f'<SiteSetting {self.key}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    username = db.Column(db.String(64), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='SUCCESS', nullable=False)

    user = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.username} at {self.timestamp}>'
