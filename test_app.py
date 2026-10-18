"""
Automated testing suite for Bitetech Technologies.
Tests public views, form submissions, customer authentication,
role-based authorization isolation, password reset workflow,
admin authentication, service management, status workflows, CSRF, and CSV export.
"""

import re
import sys
from datetime import datetime

# Configure Windows console encoding for UTF-8 compatibility
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from app import create_app
from extensions import db
from models import (
    User, Project, Course, Service, ProjectCategory,
    ProjectEnquiry, CourseEnquiry, ServiceEnquiry, ContactMessage,
    PasswordResetToken
)

def extract_csrf_token(html_text):
    match = re.search(r'name=["\']csrf_token["\'][^>]*?value=["\']([^"\']+)["\']', html_text)
    if not match:
        match = re.search(r'value=["\']([^"\']+)["\'][^>]*?name=["\']csrf_token["\']', html_text)
    return match.group(1) if match else None

def run_tests():
    print("=" * 65)
    print("BITETECH TECHNOLOGIES -- AUTOMATED FULL SYSTEM TEST SUITE")
    print("=" * 65)

    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = True  # Keep CSRF enabled to test true security

    client = app.test_client()

    with app.app_context():
        # -------------------------------------------------------------
        # 1. Test Public Routes
        # -------------------------------------------------------------
        public_routes = [
            ('/', 'Home'),
            ('/about', 'About Us'),
            ('/projects', 'Projects Catalog'),
            ('/projects/mini', 'Mini Projects (Rs 599)'),
            ('/projects/major', 'Major Projects (Rs 1,000)'),
            ('/courses', 'Online Classes Catalog'),
            ('/services', 'Services & Quotations Catalog'),
            ('/portfolio', 'Demonstration Portfolio'),
            ('/contact', 'Contact Desk'),
            ('/faq', 'FAQ Desk'),
            ('/privacy-policy', 'Privacy Policy'),
            ('/terms', 'Terms & Conditions'),
            ('/refund-policy', 'Refund Policy'),
            ('/project-delivery-policy', 'Project Delivery Policy'),
            ('/hosting-renewal-policy', 'Hosting & Renewal Policy'),
            ('/login', 'Customer Login View'),
            ('/register', 'Customer Registration View'),
            ('/forgot-password', 'Customer Forgot Password View')
        ]

        print("\n[*] 1. Testing Public Route Availability & HTTP 200 Status...")
        for endpoint, name in public_routes:
            resp = client.get(endpoint)
            assert resp.status_code == 200, f"Failed {name} ({endpoint}): HTTP {resp.status_code}"
            print(f"  [PASS] {name} ({endpoint}) -> HTTP {resp.status_code}")

        # -------------------------------------------------------------
        # 2. Test Detail Routes
        # -------------------------------------------------------------
        print("\n[*] 2. Testing Item Detail Views...")
        first_project = Project.query.first()
        assert first_project is not None, "No project in DB to test detail view"
        p_resp = client.get(f'/projects/{first_project.slug}')
        assert p_resp.status_code == 200, f"Failed project detail ({first_project.slug})"
        print(f"  [PASS] Project Detail (/projects/{first_project.slug}) -> HTTP 200")

        first_course = Course.query.first()
        assert first_course is not None, "No course in DB to test detail view"
        c_resp = client.get(f'/courses/{first_course.slug}')
        assert c_resp.status_code == 200, f"Failed course detail ({first_course.slug})"
        print(f"  [PASS] Course Detail (/courses/{first_course.slug}) -> HTTP 200")

        first_service = Service.query.first()
        assert first_service is not None, "No service in DB to test detail view"
        s_resp = client.get(f'/services/{first_service.slug}')
        assert s_resp.status_code == 200, f"Failed service detail ({first_service.slug})"
        print(f"  [PASS] Service Detail (/services/{first_service.slug}) -> HTTP 200")

        # -------------------------------------------------------------
        # 3. Test Public Form Submissions
        # -------------------------------------------------------------
        print("\n[*] 3. Testing Public Form Submissions & DB Persistence...")
        
        # 3a. Contact Form
        contact_page = client.get('/contact')
        csrf_token = extract_csrf_token(contact_page.data.decode('utf-8'))
        assert csrf_token is not None, "Could not extract CSRF token from contact page"
        test_msg_count = ContactMessage.query.count()
        post_resp = client.post('/contact', data={
            'csrf_token': csrf_token,
            'name': 'Pooja Sharma',
            'email': 'pooja@example.com',
            'phone': '9876543210',
            'subject': 'Python Course Enquiry',
            'service': 'Python Mini-Project Development',
            'budget': '₹599 - ₹1,000',
            'message': 'Interested in Python fundamentals with live weekend support.',
            'website_hp': ''
        }, follow_redirects=True)
        assert post_resp.status_code == 200
        assert ContactMessage.query.count() == test_msg_count + 1
        print("  [PASS] Contact form submitted with CSRF -> persisted in DB.")

        # 3b. Project Enquiry Form
        p_detail_page = client.get(f'/projects/{first_project.slug}')
        csrf_token = extract_csrf_token(p_detail_page.data.decode('utf-8'))
        p_enq_count = ProjectEnquiry.query.count()
        post_p = client.post(f'/projects/{first_project.slug}', data={
            'csrf_token': csrf_token,
            'project_id': first_project.id,
            'client_name': 'Kunal Verma',
            'client_email': 'kunal@example.com',
            'client_phone': '9812345678',
            'project_type': 'Ready-to-Run Reference Project',
            'budget_range': '₹599 - ₹1,000',
            'requirements': 'Need automated verification of student attendance records.',
            'website_hp': ''
        }, follow_redirects=True)
        assert post_p.status_code == 200
        assert ProjectEnquiry.query.count() == p_enq_count + 1
        print("  [PASS] Project enquiry submitted -> persisted in DB.")

        # 3c. Course Enquiry Form
        c_detail_page = client.get(f'/courses/{first_course.slug}')
        csrf_token = extract_csrf_token(c_detail_page.data.decode('utf-8'))
        c_enq_count = CourseEnquiry.query.count()
        post_c = client.post(f'/courses/{first_course.slug}', data={
            'csrf_token': csrf_token,
            'course_id': first_course.id,
            'student_name': 'Rohit Gupta',
            'student_email': 'rohit@example.com',
            'student_phone': '9871234567',
            'preferred_batch': 'Weekend Batches (Sat-Sun)',
            'learning_mode': 'Online Live Mentoring (Zoom/Meet)',
            'message': 'Beginner looking to learn Python from scratch.',
            'website_hp': ''
        }, follow_redirects=True)
        assert post_c.status_code == 200
        assert CourseEnquiry.query.count() == c_enq_count + 1
        print("  [PASS] Course registration enquiry submitted -> persisted in DB.")

        # 3d. Service Quotation Form
        s_detail_page = client.get(f'/services/{first_service.slug}')
        csrf_token = extract_csrf_token(s_detail_page.data.decode('utf-8'))
        s_enq_count = ServiceEnquiry.query.count()
        post_s = client.post(f'/services/{first_service.slug}', data={
            'csrf_token': csrf_token,
            'service_id': first_service.id,
            'client_name': 'Meera Patel',
            'client_email': 'meera@store.in',
            'client_phone': '9899887766',
            'project_title': 'E-Commerce Boutique Website',
            'budget_range': '₹5,000 - ₹7,000',
            'timeline': '2-3 Weeks',
            'project_requirements': 'Product catalog with WhatsApp ordering and hosting setup.',
            'website_hp': ''
        }, follow_redirects=True)
        assert post_s.status_code == 200
        assert ServiceEnquiry.query.count() == s_enq_count + 1
        print("  [PASS] Service quotation enquiry submitted -> persisted in DB.")

        # -------------------------------------------------------------
        # 4. Customer Portal: Registration, Login & Isolation
        # -------------------------------------------------------------
        print("\n[*] 4. Testing Customer Registration, Portal & Access Isolation...")
        
        # Clean up any previous test customer
        test_uname = 'autotest_student'
        existing_test_u = User.query.filter_by(username=test_uname).first()
        if existing_test_u:
            # Delete linked records if any
            PasswordResetToken.query.filter_by(user_id=existing_test_u.id).delete()
            db.session.delete(existing_test_u)
            db.session.commit()

        # Registration
        reg_page = client.get('/register')
        csrf_token = extract_csrf_token(reg_page.data.decode('utf-8'))
        reg_resp = client.post('/register', data={
            'csrf_token': csrf_token,
            'username': test_uname,
            'email': 'autotest_student@example.com',
            'full_name': 'Auto Test Student',
            'phone': '9870001122',
            'password': 'SecureStudentPass2026!',
            'confirm_password': 'SecureStudentPass2026!',
            'agree_terms': 'y'
        }, follow_redirects=True)
        assert reg_resp.status_code == 200
        test_cust = User.query.filter_by(username=test_uname).first()
        assert test_cust is not None, "Customer was not created in database!"
        assert test_cust.role == 'customer', f"Expected role='customer', got {test_cust.role}"
        print("  [PASS] Customer registered successfully with hashed password.")

        # Log out auto-logged in session from registration to test explicit login
        client.get('/logout', follow_redirects=True)

        # Customer Login
        login_page = client.get('/login')
        csrf_token = extract_csrf_token(login_page.data.decode('utf-8'))
        assert csrf_token is not None, "Could not extract CSRF token from customer login page"
        cust_login_resp = client.post('/login', data={
            'csrf_token': csrf_token,
            'username_or_email': test_uname,
            'password': 'SecureStudentPass2026!'
        }, follow_redirects=True)
        assert cust_login_resp.status_code == 200
        assert b"Student & Customer Portal" in cust_login_resp.data or b"Dashboard" in cust_login_resp.data
        print("  [PASS] Customer login successful -> Customer dashboard loaded.")

        # Customer Dashboard View
        dash_resp = client.get('/dashboard')
        assert dash_resp.status_code == 200
        assert b"Auto Test Student" in dash_resp.data or b"autotest_student" in dash_resp.data
        print("  [PASS] Customer dashboard displays authenticated user profile.")

        # Customer Profile Update
        csrf_token = extract_csrf_token(dash_resp.data.decode('utf-8'))
        prof_resp = client.post('/profile/update', data={
            'csrf_token': csrf_token,
            'full_name': 'Auto Test Student Updated',
            'phone': '9870009999'
        }, follow_redirects=True)
        assert prof_resp.status_code == 200
        db.session.refresh(test_cust)
        assert test_cust.full_name == 'Auto Test Student Updated'
        assert test_cust.phone == '9870009999'
        print("  [PASS] Customer updated profile information successfully.")

        # Authorization Isolation Check: Customer MUST NOT access admin routes
        print("\n[*] 5. Testing Authorization Isolation (Customer cannot access Admin area)...")
        admin_blocked_resp = client.get('/admin/dashboard', follow_redirects=False)
        assert admin_blocked_resp.status_code in (301, 302)
        assert '/admin/login' in admin_blocked_resp.headers['Location']
        print("  [PASS] Customer access to /admin/dashboard blocked -> Redirected to /admin/login.")

        admin_svc_blocked = client.get('/admin/services', follow_redirects=False)
        assert admin_svc_blocked.status_code in (301, 302)
        print("  [PASS] Customer access to /admin/services blocked.")

        # Customer Logout
        cust_logout = client.get('/logout', follow_redirects=True)
        assert cust_logout.status_code == 200
        # Verify subsequent /dashboard access is redirected to /login
        dash_after_logout = client.get('/dashboard', follow_redirects=False)
        assert dash_after_logout.status_code in (301, 302)
        assert '/login' in dash_after_logout.headers['Location']
        print("  [PASS] Customer logout invalidated session successfully.")

        # -------------------------------------------------------------
        # 6. Password Reset Workflow
        # -------------------------------------------------------------
        print("\n[*] 6. Testing Customer Password Recovery Workflow...")
        forgot_page = client.get('/forgot-password')
        csrf_token = extract_csrf_token(forgot_page.data.decode('utf-8'))
        post_forgot = client.post('/forgot-password', data={
            'csrf_token': csrf_token,
            'email': 'autotest_student@example.com'
        }, follow_redirects=True)
        assert post_forgot.status_code == 200
        token_obj = PasswordResetToken.query.filter_by(user_id=test_cust.id, used=False).first()
        assert token_obj is not None, "Password reset token not generated in DB!"
        print(f"  [PASS] Password reset token generated for user.")

        reset_page = client.get(f'/reset-password/{token_obj.token_hash}')
        assert reset_page.status_code == 200
        csrf_token = extract_csrf_token(reset_page.data.decode('utf-8'))
        post_reset = client.post(f'/reset-password/{token_obj.token_hash}', data={
            'csrf_token': csrf_token,
            'password': 'NewPasswordReset2026!',
            'confirm_password': 'NewPasswordReset2026!'
        }, follow_redirects=True)
        assert post_reset.status_code == 200
        assert b"Your password has been reset successfully" in post_reset.data or b"Sign in" in post_reset.data
        db.session.refresh(token_obj)
        assert token_obj.used is True, "Token was not marked as used!"

        # Verify login with new password
        login_page = client.get('/login')
        csrf_token = extract_csrf_token(login_page.data.decode('utf-8'))
        new_login = client.post('/login', data={
            'csrf_token': csrf_token,
            'username_or_email': test_uname,
            'password': 'NewPasswordReset2026!'
        }, follow_redirects=True)
        assert new_login.status_code == 200
        assert b"Student & Customer Portal" in new_login.data or b"Dashboard" in new_login.data
        print("  [PASS] Customer authenticated with newly reset password.")
        client.get('/logout')

        # -------------------------------------------------------------
        # 7. Admin Authentication & Session Management
        # -------------------------------------------------------------
        print("\n[*] 7. Testing Admin Authentication & Route Protection...")
        unauth_resp = client.get('/admin/dashboard', follow_redirects=False)
        assert unauth_resp.status_code in (302, 301)
        assert '/admin/login' in unauth_resp.headers['Location']
        print("  [PASS] Unauthenticated access to /admin/dashboard blocked.")

        # Invalid password test
        login_page = client.get('/admin/login')
        csrf_token = extract_csrf_token(login_page.data.decode('utf-8'))
        bad_login = client.post('/admin/login', data={
            'csrf_token': csrf_token,
            'username': 'admin',
            'password': 'WrongPassword123'
        }, follow_redirects=True)
        assert b"Invalid username or password" in bad_login.data
        print("  [PASS] Invalid admin credentials rejected.")

        # Valid login test
        login_page = client.get('/admin/login')
        csrf_token = extract_csrf_token(login_page.data.decode('utf-8'))
        good_login = client.post('/admin/login', data={
            'csrf_token': csrf_token,
            'username': 'admin',
            'password': 'AdminSecure2026!'
        }, follow_redirects=True)
        assert good_login.status_code == 200
        assert b"Dashboard" in good_login.data or b"Welcome back" in good_login.data
        print("  [PASS] Admin credentials accepted. Admin session active.")

        # -------------------------------------------------------------
        # 8. Authenticated Admin Views
        # -------------------------------------------------------------
        print("\n[*] 8. Testing Authenticated Admin Views...")
        admin_views = [
            ('/admin/dashboard', 'Admin Dashboard'),
            ('/admin/enquiries', 'Admin Enquiries'),
            ('/admin/projects', 'Admin Projects'),
            ('/admin/services', 'Admin Services'),
            ('/admin/customers', 'Admin Customers'),
            ('/admin/categories', 'Admin Categories'),
            ('/admin/courses', 'Admin Courses'),
            ('/admin/portfolio', 'Admin Portfolio'),
            ('/admin/faqs', 'Admin FAQs'),
            ('/admin/settings', 'Admin Settings'),
            ('/admin/audit-logs', 'Admin Audit Logs')
        ]
        for url, name in admin_views:
            resp = client.get(url)
            assert resp.status_code == 200, f"Admin view {name} ({url}) returned HTTP {resp.status_code}"
            print(f"  [PASS] {name} ({url}) -> HTTP 200")

        # -------------------------------------------------------------
        # 9. Admin Service Creation (CRUD)
        # -------------------------------------------------------------
        print("\n[*] 9. Testing Admin Service Creation...")
        svc_new_page = client.get('/admin/services/new')
        assert svc_new_page.status_code == 200
        csrf_token = extract_csrf_token(svc_new_page.data.decode('utf-8'))
        
        test_svc_slug = 'custom-flask-api-suite'
        existing_svc = Service.query.filter_by(slug=test_svc_slug).first()
        if existing_svc:
            db.session.delete(existing_svc)
            db.session.commit()

        post_svc = client.post('/admin/services/new', data={
            'csrf_token': csrf_token,
            'title': 'Custom Flask API Suite',
            'slug': test_svc_slug,
            'starting_price': '₹8,500',
            'price_integer': 8500,
            'timeline': '2 Weeks',
            'short_description': 'Enterprise RESTful API backend built with Python Flask.',
            'full_description': 'Complete microservice architecture with JWT auth and SQLite/MySQL support.',
            'features': 'JWT Authentication\nRate Limiting\nSwagger Documentation',
            'deliverables': 'Complete Source Code\nAPI Docs\nDeployment Script',
            'project_requirements': 'API specification and database schema requirements.',
            'hosting_duration': '1 Year Included',
            'domain_included': 'Custom Domain Included',
            'renewal_cost': '₹2,500/year',
            'additional_charges': 'Extra endpoints @ ₹500 each',
            'is_published': 'y',
            'is_featured': 'y'
        }, follow_redirects=True)
        assert post_svc.status_code == 200
        created_svc = Service.query.filter_by(slug=test_svc_slug).first()
        assert created_svc is not None, "Admin service was not created in database!"
        print("  [PASS] Admin service created and persisted successfully.")

        # -------------------------------------------------------------
        # 10. Enquiry Status Updates
        # -------------------------------------------------------------
        print("\n[*] 10. Testing Enquiry Status Updates with CSRF...")
        enq_page = client.get('/admin/enquiries')
        csrf_token = extract_csrf_token(enq_page.data.decode('utf-8'))
        assert csrf_token is not None, "Could not extract CSRF token from admin enquiries page"

        # Update Project Enquiry
        pe = ProjectEnquiry.query.first()
        status_resp = client.post(f'/admin/enquiries/project/{pe.id}/status', data={
            'csrf_token': csrf_token,
            'status': 'Contacted',
            'admin_notes': 'Spoke via WhatsApp, confirmed project scope.'
        }, follow_redirects=True)
        assert status_resp.status_code == 200
        db.session.refresh(pe)
        assert pe.status == 'Contacted', f"Status not updated, found {pe.status}"
        print("  [PASS] Project enquiry status updated to 'Contacted'.")

        # Update Service Enquiry
        se = ServiceEnquiry.query.first()
        if se:
            se_resp = client.post(f'/admin/enquiries/service/{se.id}/status', data={
                'csrf_token': csrf_token,
                'status': 'In Progress',
                'admin_notes': 'Sent initial quotation PDF and timeline estimate.'
            }, follow_redirects=True)
            assert se_resp.status_code == 200
            db.session.refresh(se)
            assert se.status == 'In Progress'
            print("  [PASS] Service enquiry status updated to 'In Progress'.")

        # -------------------------------------------------------------
        # 11. Test CSV Export
        # -------------------------------------------------------------
        print("\n[*] 11. Testing CSV Export Functionality...")
        csv_resp = client.get('/admin/enquiries/export')
        assert csv_resp.status_code == 200, f"CSV export returned {csv_resp.status_code}"
        assert 'text/csv' in csv_resp.content_type
        assert 'attachment; filename=' in csv_resp.headers.get('Content-Disposition', '')
        assert b"Project Enquiry" in csv_resp.data
        print("  [PASS] CSV export returned formatted spreadsheet data containing enquiries.")

        # -------------------------------------------------------------
        # 11b. Test Admin Enquiry Deletion Endpoints & Clean Up Test Entries
        # -------------------------------------------------------------
        print("\n[*] 11b. Testing Admin Enquiry Deletion Endpoints...")
        enq_page = client.get('/admin/enquiries')
        csrf_token = extract_csrf_token(enq_page.data.decode('utf-8'))

        # Delete test project enquiry
        test_pe = ProjectEnquiry.query.filter_by(client_name='Kunal Verma').first()
        if test_pe:
            del_pe_resp = client.post(f'/admin/enquiries/project/{test_pe.id}/delete', data={'csrf_token': csrf_token}, follow_redirects=True)
            assert del_pe_resp.status_code == 200
            assert ProjectEnquiry.query.get(test_pe.id) is None
            print("  [PASS] Project enquiry deleted successfully via admin delete route.")

        # Delete test service enquiry
        test_se = ServiceEnquiry.query.filter_by(client_name='Meera Patel').first()
        if test_se:
            del_se_resp = client.post(f'/admin/enquiries/service/{test_se.id}/delete', data={'csrf_token': csrf_token}, follow_redirects=True)
            assert del_se_resp.status_code == 200
            assert ServiceEnquiry.query.get(test_se.id) is None
            print("  [PASS] Service enquiry deleted successfully via admin delete route.")

        # Delete test course enquiry
        test_ce = CourseEnquiry.query.filter_by(student_name='Rohit Gupta').first()
        if test_ce:
            del_ce_resp = client.post(f'/admin/enquiries/course/{test_ce.id}/delete', data={'csrf_token': csrf_token}, follow_redirects=True)
            assert del_ce_resp.status_code == 200
            assert CourseEnquiry.query.get(test_ce.id) is None
            print("  [PASS] Course enquiry deleted successfully via admin delete route.")

        # Delete test contact message
        test_cm = ContactMessage.query.filter_by(name='Pooja Sharma').first()
        if test_cm:
            del_cm_resp = client.post(f'/admin/enquiries/contact/{test_cm.id}/delete', data={'csrf_token': csrf_token}, follow_redirects=True)
            assert del_cm_resp.status_code == 200
            assert ContactMessage.query.get(test_cm.id) is None
            print("  [PASS] Contact message deleted successfully via admin delete route.")

        # Also clean up the custom created service from section 9
        test_created_svc = Service.query.filter_by(slug='custom-flask-api-suite').first()
        if test_created_svc:
            db.session.delete(test_created_svc)
            db.session.commit()

        # Clean up autotest customer from section 4
        test_cust_cleanup = User.query.filter_by(username='autotest_student').first()
        if test_cust_cleanup:
            PasswordResetToken.query.filter_by(user_id=test_cust_cleanup.id).delete()
            db.session.delete(test_cust_cleanup)
            db.session.commit()

        # 12. Test Admin Session Revocation & Logout
        # -------------------------------------------------------------
        print("\n[*] 12. Testing Session Invalidation & Logout...")
        settings_page = client.get('/admin/settings')
        csrf_token = extract_csrf_token(settings_page.data.decode('utf-8'))
        admin_user = User.query.filter_by(username='admin').first()
        old_version = admin_user.token_version

        revoke_resp = client.post('/admin/revoke-all-sessions', data={
            'csrf_token': csrf_token
        }, follow_redirects=True)
        assert revoke_resp.status_code == 200
        db.session.refresh(admin_user)
        assert admin_user.token_version == old_version + 1
        print("  [PASS] Admin session revocation incremented token version.")

        logout_resp = client.get('/admin/logout', follow_redirects=True)
        assert logout_resp.status_code == 200
        post_logout_check = client.get('/admin/dashboard', follow_redirects=False)
        assert post_logout_check.status_code in (301, 302)
        print("  [PASS] Admin logout successfully destroyed session.")

    print("\n" + "=" * 65)
    print("ALL 12 TEST SUITES PASSED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == '__main__':
    run_tests()
