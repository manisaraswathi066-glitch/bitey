"""
Secure administrative account creation script for Bitetech Technologies.
Does not use a hardcoded public password; securely prompts for credentials
or accepts command-line arguments for automated deployments.
Supports MFA initialization.
"""

import sys
import getpass
import argparse
from app import create_app
from extensions import db
from models import AdminUser
from security import generate_totp_secret, get_totp_uri

def create_or_update_admin(username, email, password, role='admin', reset_mfa=False):
    app = create_app()
    with app.app_context():
        db.create_all()

        user = AdminUser.query.filter(
            (AdminUser.username == username) | (AdminUser.email == email)
        ).first()

        if user:
            print(f"[*] Admin user '{user.username}' ({user.email}) already exists.")
            confirm = input("Would you like to update this user's password/MFA? (y/N): ").strip().lower()
            if confirm in ('y', 'yes'):
                user.set_password(password)
                user.role = role
                user.is_active = True
                user.failed_logins = 0
                user.locked_until = None
                if reset_mfa:
                    secret = generate_totp_secret()
                    user.mfa_secret = secret
                    user.mfa_enabled = True
                    print(f"[*] MFA Reset. New TOTP Secret: {secret}")
                db.session.commit()
                print(f"[OK] Account updated successfully for admin '{user.username}'.")
            else:
                print("[-] No changes made.")
            return

        # Provision new admin
        secret = generate_totp_secret()
        new_admin = AdminUser(
            username=username,
            email=email,
            role=role,
            is_active=True,
            mfa_secret=secret,
            mfa_enabled=False  # Requires first login setup or verification
        )
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        
        print(f"[OK] Admin user '{username}' ({email}) created successfully!")
        print(f"[*] Provisioned MFA Secret: {secret}")
        print(f"[*] On first sign-in, navigate to /admin/setup-mfa to activate your Authenticator app.")

def main():
    parser = argparse.ArgumentParser(description="Create or reset an administrator account for Bitetech Technologies.")
    parser.add_argument('--username', help="Admin username")
    parser.add_argument('--email', help="Admin email address")
    parser.add_argument('--password', help="Admin password (will prompt securely if not provided)")
    parser.add_argument('--role', default='admin', help="User role (default: admin)")
    parser.add_argument('--reset-mfa', action='store_true', help="Reset and regenerate MFA secret")
    
    args = parser.parse_args()

    username = args.username
    email = args.email
    password = args.password
    role = args.role
    reset_mfa = args.reset_mfa

    if not username:
        username = input("Enter Admin Username: ").strip()
        while not username:
            print("Username cannot be empty.")
            username = input("Enter Admin Username: ").strip()

    if not email:
        email = input("Enter Admin Email: ").strip()
        while '@' not in email or '.' not in email:
            print("Please enter a valid email address.")
            email = input("Enter Admin Email: ").strip()

    if not password:
        password = getpass.getpass("Enter Admin Password (min 6 chars): ")
        while len(password) < 6:
            print("Password must be at least 6 characters.")
            password = getpass.getpass("Enter Admin Password (min 6 chars): ")
        
        password_confirm = getpass.getpass("Confirm Admin Password: ")
        while password != password_confirm:
            print("Passwords do not match. Try again.")
            password = getpass.getpass("Enter Admin Password (min 6 chars): ")
            password_confirm = getpass.getpass("Confirm Admin Password: ")

    create_or_update_admin(username, email, password, role, reset_mfa)

if __name__ == '__main__':
    main()
