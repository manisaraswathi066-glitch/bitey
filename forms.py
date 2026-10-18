from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, TextAreaField, 
    SelectField, IntegerField, HiddenField, SubmitField
)
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, EqualTo

# ----------------- AUTHENTICATION FORMS -----------------

class AdminLoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired(), Length(3, 100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, 100)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In to Admin Panel')

class CustomerLoginForm(FlaskForm):
    username_or_email = StringField('Email Address or Username', validators=[DataRequired(), Length(3, 120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, 128)])
    remember_me = BooleanField('Keep me signed in')
    submit = SubmitField('Sign In to Account')

class CustomerRegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone / WhatsApp Number', validators=[
        DataRequired(), 
        Length(min=7, max=20),
        Regexp(r'^[0-9+\-\s()]+$', message="Please enter a valid phone or WhatsApp number.")
    ])
    username = StringField('Choose Username', validators=[
        DataRequired(), 
        Length(min=3, max=30),
        Regexp(r'^[a-zA-Z0-9_]+$', message="Username must contain only letters, numbers, and underscores.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message="Passwords do not match.")
    ])
    agree_terms = BooleanField('I agree to the Terms & Conditions and Privacy Policy', validators=[DataRequired(message="You must accept the terms.")])
    submit = SubmitField('Create Customer Account')

class ForgotPasswordRequestForm(FlaskForm):
    email = StringField('Registered Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Send Password Reset Instructions')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), 
        EqualTo('password', message="Passwords do not match.")
    ])
    submit = SubmitField('Reset Password & Sign In')

class CustomerProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone / WhatsApp Number', validators=[
        DataRequired(), 
        Length(min=7, max=20),
        Regexp(r'^[0-9+\-\s()]+$', message="Please enter a valid phone number.")
    ])
    submit = SubmitField('Update Profile Information')

# ----------------- PUBLIC ENQUIRY FORMS -----------------

class ContactForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone / WhatsApp Number', validators=[
        DataRequired(), 
        Length(min=7, max=20),
        Regexp(r'^[0-9+\-\s()]+$', message="Please enter a valid phone number.")
    ])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=3, max=200)])
    service = SelectField('Select Service Required', choices=[
        ('Python Mini-Project Development', 'Python Mini-Project Development (Starts ₹599)'),
        ('Python Major Project Development', 'Python Major Project Development (Starts ₹1,000)'),
        ('Shop or Small Business Website', 'Shop or Small Business Website (Starts ₹5,000)'),
        ('Website with Hosting & Domain', 'Website with Hosting (Starts ₹7,000)'),
        ('Student Project Guidance & Debugging', 'Student Project Guidance & Debugging'),
        ('Database Integration (MySQL / SQLite)', 'Database Integration (MySQL / SQLite)'),
        ('Online Programming Classes', 'Online Programming Classes'),
        ('General Inquiry', 'General Inquiry / Consultation')
    ], default='Python Mini-Project Development')
    budget = SelectField('Estimated Budget', choices=[
        ('₹599 - ₹1,000', '₹599 - ₹1,000 (Mini Projects)'),
        ('₹1,000 - ₹2,500', '₹1,000 - ₹2,500 (Major Projects / Scripts)'),
        ('₹5,000 - ₹7,000', '₹5,000 - ₹7,000 (Shop Websites)'),
        ('₹7,000 - ₹15,000', '₹7,000 - ₹15,000 (Website with Hosting)'),
        ('Flexible / To Discuss', 'Flexible / To Discuss')
    ], default='₹599 - ₹1,000')
    message = TextAreaField('Project Requirements or Message', validators=[DataRequired(), Length(min=10, max=3000)])
    website_hp = StringField('Website', validators=[Optional()])  # Anti-spam Honeypot
    submit = SubmitField('Send Message & Request Quote')

class ProjectEnquiryForm(FlaskForm):
    project_id = HiddenField('Project ID', validators=[Optional()])
    client_name = StringField('Your Name', validators=[DataRequired(), Length(min=2, max=100)])
    client_email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    client_phone = StringField('Contact / WhatsApp Number', validators=[
        DataRequired(), Length(min=7, max=20),
        Regexp(r'^[0-9+\-\s()]+$', message="Please enter a valid phone number.")
    ])
    project_type = SelectField('Project Scope', choices=[
        ('Python Mini Project (₹599)', 'Python Mini Project (Starting from ₹599)'),
        ('Python Major Project (₹1,000)', 'Python Major Project (Starting from ₹1,000)'),
        ('Ready-to-Run Reference Project', 'Ready-to-Run Reference Project'),
        ('Customization of Existing Demo', 'Customization of Existing Demo'),
        ('Academic / College Project with Documentation', 'Academic / College Project with Documentation'),
        ('Code Debugging / Integration Support', 'Code Debugging / Integration Support')
    ], default='Python Mini Project (₹599)')
    budget_range = SelectField('Budget', choices=[
        ('₹599 - ₹1,000', '₹599 - ₹1,000 (Mini Projects)'),
        ('₹1,000 - ₹2,500', '₹1,000 - ₹2,500 (Major Projects)'),
        ('₹2,500 - ₹5,000', '₹2,500 - ₹5,000 (Advanced Systems)'),
        ('₹5,000+', '₹5,000+ (Custom Scope)')
    ], default='₹599 - ₹1,000')
    requirements = TextAreaField('Detailed Requirements & Timeline', validators=[DataRequired(), Length(min=10, max=3000)])
    website_hp = StringField('Website', validators=[Optional()])  # Anti-spam Honeypot
    submit = SubmitField('Submit Project Enquiry')

class CourseEnquiryForm(FlaskForm):
    course_id = HiddenField('Course ID', validators=[Optional()])
    student_name = StringField('Student Name', validators=[DataRequired(), Length(min=2, max=100)])
    student_email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    student_phone = StringField('WhatsApp / Mobile Number', validators=[
        DataRequired(), Length(min=7, max=20),
        Regexp(r'^[0-9+\-\s()]+$', message="Please enter a valid phone number.")
    ])
    preferred_batch = SelectField('Preferred Batch Timing', choices=[
        ('Weekend Batches (Sat-Sun)', 'Weekend Batches (Sat-Sun)'),
        ('Weekday Evenings (Mon-Fri 7PM-9PM)', 'Weekday Evenings (Mon-Fri 7PM-9PM)'),
        ('Weekday Mornings (Mon-Fri 8AM-10AM)', 'Weekday Mornings (Mon-Fri 8AM-10AM)'),
        ('1-on-1 Personalized Mentoring', '1-on-1 Personalized Mentoring'),
        ('Self-Paced with Mentor Check-ins', 'Self-Paced with Mentor Check-ins')
    ], default='Weekend Batches (Sat-Sun)')
    learning_mode = SelectField('Preferred Learning Mode', choices=[
        ('Online Live Mentoring (Zoom/Meet)', 'Online Live Mentoring (Zoom/Meet)'),
        ('Recorded Sessions with Live Doubt Clearing', 'Recorded Sessions with Live Doubt Clearing'),
        ('Classroom / Offline (Subject to Availability)', 'Classroom / Offline (Subject to Availability)')
    ], default='Online Live Mentoring (Zoom/Meet)')
    message = TextAreaField('Prior Experience & Goals (Optional)', validators=[Optional(), Length(max=1000)])
    website_hp = StringField('Website', validators=[Optional()])  # Anti-spam Honeypot
    submit = SubmitField('Join Class / Submit Course Enquiry')

class ServiceEnquiryForm(FlaskForm):
    service_id = HiddenField('Service ID', validators=[Optional()])
    client_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    client_email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    client_phone = StringField('WhatsApp / Phone Number', validators=[
        DataRequired(), Length(min=7, max=20),
        Regexp(r'^[0-9+\-\s()]+$', message="Please enter a valid phone number.")
    ])
    project_title = StringField('Project or Business Name', validators=[DataRequired(), Length(min=2, max=200)])
    budget_range = SelectField('Estimated Budget Range', choices=[
        ('₹5,000 - ₹7,000', '₹5,000 - ₹7,000 (Small Business / Shop Website)'),
        ('₹7,000 - ₹12,000', '₹7,000 - ₹12,000 (Website with Hosting & Domain)'),
        ('₹12,000 - ₹25,000', '₹12,000 - ₹25,000 (Custom Web App / Portal)'),
        ('₹25,000+', '₹25,000+ (Complete Software Suite)')
    ], default='₹5,000 - ₹7,000')
    target_timeline = StringField('Target Completion Timeline', default='Within 1-2 Weeks', validators=[Optional(), Length(max=100)])
    project_requirements = TextAreaField('Detailed Requirements & Desired Features', validators=[DataRequired(), Length(min=10, max=3000)])
    website_hp = StringField('Website', validators=[Optional()])
    submit = SubmitField('Submit Quotation Request')

# ----------------- ADMIN MANAGEMENT FORMS -----------------

class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(max=200)])
    slug = StringField('URL Slug', validators=[DataRequired(), Length(max=200)])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    project_type = SelectField('Project Classification', choices=[
        ('Mini', 'Python Mini Project (Starting from ₹599)'),
        ('Major', 'Python Major Project (Starting from ₹1,000)')
    ], default='Mini')
    starting_price = IntegerField('Starting Price (₹ INR)', default=599, validators=[DataRequired()])
    price_range = StringField('Display Price Tag (e.g. From ₹599)', default='From ₹599', validators=[DataRequired(), Length(max=100)])
    short_description = TextAreaField('Short Summary (Max 350 chars)', validators=[DataRequired(), Length(max=350)])
    full_description = TextAreaField('Full Description & Architecture', validators=[DataRequired()])
    problem_statement = TextAreaField('Problem Statement & Background', validators=[Optional()])
    features = TextAreaField('Key Features (One feature per line)', validators=[Optional()])
    deliverables = TextAreaField('Expected Deliverables (One per line)', validators=[Optional()])
    tech_stack = StringField('Tech Stack (Comma-separated, e.g. Python, Flask, MySQL)', validators=[DataRequired(), Length(max=255)])
    source_code_included = BooleanField('Source Code Included in Offering', default=True)
    availability_status = SelectField('Availability Status', choices=[
        ('Available', 'Available (Direct Delivery)'),
        ('Custom Order', 'Custom Order / On Request'),
        ('Archived', 'Archived / Hidden')
    ], default='Available')
    is_demo = BooleanField('Mark as Demonstration Project (Demo)', default=True)
    is_published = BooleanField('Published (Visible to Public)', default=True)
    is_featured = BooleanField('Featured on Homepage', default=False)
    image_url = StringField('Image / Preview URL', validators=[Optional(), Length(max=500)])
    demo_link = StringField('Live Demo or Repository Link', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Project')

class ServiceForm(FlaskForm):
    title = StringField('Service Name', validators=[DataRequired(), Length(max=200)])
    slug = StringField('URL Slug', validators=[DataRequired(), Length(max=200)])
    starting_price = StringField('Display Starting Price (e.g. ₹5,000, ₹7,000)', validators=[DataRequired(), Length(max=100)])
    price_integer = IntegerField('Starting Price Numeric (₹ INR)', default=5000, validators=[DataRequired()])
    timeline = StringField('Estimated Timeline (e.g. 5-7 Working Days)', default='5-7 Working Days', validators=[DataRequired(), Length(max=100)])
    short_description = TextAreaField('Short Summary (Max 350 chars)', validators=[DataRequired(), Length(max=350)])
    full_description = TextAreaField('Full Service Description', validators=[DataRequired()])
    features = TextAreaField('Features Included (One feature per line)', validators=[Optional()])
    deliverables = TextAreaField('Expected Deliverables (One per line)', validators=[Optional()])
    project_requirements = TextAreaField('Prerequisites / Information Needed from Client', validators=[Optional()])
    hosting_duration = StringField('Hosting Duration (e.g. 1 Year Included / Not Included)', default='Configurable per package', validators=[Optional(), Length(max=200)])
    domain_included = StringField('Domain Details (e.g. .com / .in domain included for 1st year)', default='Included or provided by client', validators=[Optional(), Length(max=200)])
    renewal_cost = StringField('Renewal Costs & Terms (e.g. ₹2,500/year after first year)', default='Standard renewal fees apply after year 1', validators=[Optional(), Length(max=200)])
    additional_charges = StringField('Additional Services & Add-on Charges', default='Payment gateway, extra pages, and maintenance charged extra', validators=[Optional(), Length(max=255)])
    is_published = BooleanField('Published (Visible to Public)', default=True)
    is_featured = BooleanField('Featured on Homepage', default=False)
    submit = SubmitField('Save Service Package')

class CourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired(), Length(max=200)])
    slug = StringField('URL Slug', validators=[DataRequired(), Length(max=200)])
    level = SelectField('Level', choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Comprehensive Track', 'Comprehensive Track')
    ], default='Beginner')
    duration = StringField('Duration (e.g. 4 Weeks, 30 Hours)', validators=[DataRequired(), Length(max=100)])
    price = StringField('Display Fee (e.g. ₹599, ₹899, ₹1,499)', validators=[DataRequired(), Length(max=100)])
    fee_integer = IntegerField('Course Fee Numeric (₹ INR)', default=899, validators=[DataRequired()])
    delivery_mode = SelectField('Delivery Mode', choices=[
        ('Online Live Mentoring', 'Online Live Mentoring'),
        ('Offline Classroom', 'Offline Classroom'),
        ('Hybrid', 'Hybrid (Online + Mentorship)')
    ], default='Online Live Mentoring')
    class_schedule = StringField('Class Schedule (e.g. Weekend Batches)', default='Weekend & Evening Batches Available', validators=[DataRequired(), Length(max=150)])
    teaching_format = StringField('Teaching Format', default='Live Screen-Share, Code Review, and Hands-on Tasks', validators=[DataRequired(), Length(max=150)])
    status = SelectField('Enrollment Status', choices=[
        ('Enrolling', 'Enrolling Now'),
        ('Upcoming', 'Upcoming Batch'),
        ('Closed', 'Batch Full / Closed')
    ], default='Enrolling')
    short_description = TextAreaField('Short Description', validators=[DataRequired(), Length(max=350)])
    syllabus = TextAreaField('Syllabus (Format each line as: Module X: Title | Detail description)', validators=[DataRequired()])
    outcomes = TextAreaField('Learning Outcomes (One per line)', validators=[Optional()])
    prerequisites = StringField('Prerequisites', default='Basic computer literacy; no prior coding required', validators=[Optional(), Length(max=255)])
    badge_text = StringField('Badge Text (e.g. Best for Beginners, High Demand)', validators=[Optional(), Length(max=50)])
    is_published = BooleanField('Published', default=True)
    is_featured = BooleanField('Featured on Homepage', default=False)
    submit = SubmitField('Save Course')

class PortfolioForm(FlaskForm):
    title = StringField('Portfolio Title', validators=[DataRequired(), Length(max=200)])
    category = StringField('Category (e.g. Web App, Automation, Data Management)', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    client_type = StringField('Project Type / Context', default='Engineering Reference Implementation', validators=[Optional(), Length(max=150)])
    features = TextAreaField('Key Highlights (One per line)', validators=[Optional()])
    technologies = StringField('Technologies Used (Comma-separated)', validators=[DataRequired(), Length(max=255)])
    image_url = StringField('Preview / Thumbnail URL', validators=[Optional(), Length(max=500)])
    live_url = StringField('Live Link / Demo Link', validators=[Optional(), Length(max=500)])
    is_published = BooleanField('Published', default=True)
    submit = SubmitField('Save Portfolio Item')

class FAQForm(FlaskForm):
    question = StringField('Question', validators=[DataRequired(), Length(max=300)])
    answer = TextAreaField('Answer', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('General', 'General'),
        ('Projects', 'Python Projects'),
        ('Classes', 'Online Classes'),
        ('Services & Hosting', 'Services & Hosting Packages'),
        ('Payments & Support', 'Payments & Delivery Support')
    ], default='General')
    display_order = IntegerField('Display Order', default=0)
    is_published = BooleanField('Published', default=True)
    submit = SubmitField('Save FAQ')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('URL Slug', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')

class SiteSettingsForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    company_email = StringField('Official Email', validators=[DataRequired(), Email()])
    company_phone = StringField('Contact Number', validators=[DataRequired()])
    whatsapp_number = StringField('WhatsApp Number (with country code, e.g. 917418332912)', validators=[DataRequired()])
    starting_price = StringField('Starting Project Price', validators=[DataRequired()])
    hero_headline = StringField('Hero Headline', validators=[DataRequired()])
    hero_subheadline = TextAreaField('Hero Subheadline', validators=[DataRequired()])
    about_text = TextAreaField('About Summary', validators=[DataRequired()])
    mission_text = TextAreaField('Mission Statement', validators=[DataRequired()])
    vision_text = TextAreaField('Vision Statement', validators=[DataRequired()])
    privacy_policy = TextAreaField('Privacy Policy Content', validators=[DataRequired()])
    terms_conditions = TextAreaField('Terms of Service Content', validators=[DataRequired()])
    refund_policy = TextAreaField('Refund Policy & Delivery Conditions', validators=[DataRequired()])
    project_delivery_policy = TextAreaField('Project Delivery & Revision Policy Content', validators=[Optional()])
    hosting_renewal_policy = TextAreaField('Hosting & Renewal Policy Content', validators=[Optional()])
    incident_mode = SelectField('Defensive Incident Response Mode', choices=[
        ('normal', 'Normal Operations (Full Access)'),
        ('read_only', 'Read-Only / Maintenance Mode (Public viewing enabled, forms paused)'),
        ('lockdown', 'Emergency Lockdown Mode (Admin login blocked except CLI, forms paused)')
    ], default='normal')
    submit = SubmitField('Save All Site Settings')

class MFAVerifyForm(FlaskForm):
    code = StringField('6-Digit Authenticator Code', validators=[
        DataRequired(),
        Length(min=6, max=6, message="Authenticator code must be exactly 6 digits."),
        Regexp(r'^\d{6}$', message="Code must contain only numeric digits.")
    ])
    submit = SubmitField('Verify & Sign In')

class MFASetupForm(FlaskForm):
    secret = HiddenField('Secret', validators=[DataRequired()])
    code = StringField('Verification Code from Authenticator App', validators=[
        DataRequired(),
        Length(min=6, max=6, message="Authenticator code must be exactly 6 digits."),
        Regexp(r'^\d{6}$', message="Code must contain only numeric digits.")
    ])
    submit = SubmitField('Confirm & Enable MFA')

class ConfirmPasswordForm(FlaskForm):
    password = PasswordField('Confirm Current Admin Password', validators=[DataRequired()])
    submit = SubmitField('Verify & Proceed')
