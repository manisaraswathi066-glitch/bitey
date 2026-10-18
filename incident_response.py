"""
Bitetech Technologies — Incident Response & Defensive Operations CLI.
Allows an authorized operator to:
- Inspect security posture and recent audit events
- Switch incident mode: normal / read_only / lockdown
- Revoke active administrator sessions immediately
- Unlock accounts locked by rate limits
- Generate cryptographically secure replacement secret keys
Preserves all security logs and evidence for forensic analysis.
"""

import sys
import secrets
import argparse
from datetime import datetime, timezone
from app import create_app
from extensions import db
from models import AdminUser, SiteSetting, AuditLog
from security import log_security_event

def show_status():
    app = create_app()
    with app.app_context():
        mode = SiteSetting.get_setting('incident_mode', 'normal')
        total_admins = AdminUser.query.count()
        locked_admins = AdminUser.query.filter(AdminUser.locked_until != None).all()
        mfa_enabled_count = AdminUser.query.filter_by(mfa_enabled=True).count()
        recent_events = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

        print("=" * 65)
        print("BITETECH TECHNOLOGIES — SECURITY INCIDENT STATUS REPORT")
        print("=" * 65)
        print(f"Current Defensive Mode : {mode.upper()}")
        print(f"Total Administrators   : {total_admins} (MFA Active: {mfa_enabled_count})")
        print(f"Locked Accounts        : {len(locked_admins)}")
        for la in locked_admins:
            print(f"  - {la.username} ({la.email}): locked until {la.locked_until}")
        
        print("\nRecent Security Audit Logs (Last 10):")
        print("-" * 65)
        for ev in recent_events:
            print(f"[{ev.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {ev.status:7} | {ev.action:25} | User: {ev.username or 'Anon':12} | IP: {ev.ip_address}")
            if ev.details:
                print(f"    Details: {ev.details[:80]}")
        print("=" * 65)

def set_incident_mode(new_mode):
    if new_mode not in ('normal', 'read_only', 'lockdown'):
        print(f"[-] Invalid mode '{new_mode}'. Options: normal, read_only, lockdown")
        return

    app = create_app()
    with app.app_context():
        old_mode = SiteSetting.get_setting('incident_mode', 'normal')
        SiteSetting.set_setting('incident_mode', new_mode, 'Incident response mode')
        
        log_security_event(
            'INCIDENT_MODE_CLI_OVERRIDE',
            details=f"Operator changed incident mode from '{old_mode}' to '{new_mode}' via CLI",
            status='WARNING'
        )
        print(f"[OK] Platform incident mode updated: {old_mode.upper()} -> {new_mode.upper()}")
        if new_mode == 'read_only':
            print("  [*] Public forms are now PAUSED. Public viewing remains active.")
        elif new_mode == 'lockdown':
            print("  [*] Emergency lockdown active. Web logins and public submissions are BLOCKED.")

def revoke_sessions(username=None):
    app = create_app()
    with app.app_context():
        if username:
            user = AdminUser.query.filter_by(username=username).first()
            if not user:
                print(f"[-] User '{username}' not found.")
                return
            user.token_version = (user.token_version or 1) + 1
            db.session.commit()
            log_security_event('SESSIONS_REVOKED_CLI', user=user, details="Sessions revoked via CLI")
            print(f"[OK] Sessions revoked for user '{username}'. New token version: v{user.token_version}")
        else:
            admins = AdminUser.query.all()
            for a in admins:
                a.token_version = (a.token_version or 1) + 1
            db.session.commit()
            log_security_event('ALL_SESSIONS_REVOKED_CLI', details="All admin sessions revoked via CLI")
            print(f"[OK] All active administrator sessions ({len(admins)} users) revoked successfully.")

def reset_lockout(username):
    app = create_app()
    with app.app_context():
        user = AdminUser.query.filter_by(username=username).first()
        if not user:
            print(f"[-] User '{username}' not found.")
            return
        user.locked_until = None
        user.failed_logins = 0
        db.session.commit()
        log_security_event('LOCKOUT_RESET_CLI', user=user, details="Lockout manually cleared via CLI")
        print(f"[OK] Lockout cleared for user '{username}'. Failed login count reset to 0.")

def generate_secret_key():
    new_key = secrets.token_hex(32)
    print("=" * 65)
    print("CRYPTOGRAPHICALLY SECURE FLASK SECRET KEY")
    print("=" * 65)
    print(f"SECRET_KEY={new_key}")
    print("\nTo apply: Update SECRET_KEY in your .env file and restart the server.")
    print("=" * 65)

def main():
    parser = argparse.ArgumentParser(description="Bitetech Technologies Incident Response & Defensive Operations CLI")
    parser.add_argument('--status', action='store_true', help="Display current security posture, locked accounts, and recent events")
    parser.add_argument('--set-mode', choices=['normal', 'read_only', 'lockdown'], help="Switch platform incident response mode")
    parser.add_argument('--revoke-sessions', nargs='?', const='all', help="Revoke active sessions for all users or a specific username")
    parser.add_argument('--reset-lockout', help="Reset lockout and failed login counter for a specific username")
    parser.add_argument('--rotate-secret', action='store_true', help="Generate a secure replacement SECRET_KEY")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.set_mode:
        set_incident_mode(args.set_mode)
    elif args.revoke_sessions:
        target = None if args.revoke_sessions == 'all' else args.revoke_sessions
        revoke_sessions(target)
    elif args.reset_lockout:
        reset_lockout(args.reset_lockout)
    elif args.rotate_secret:
        generate_secret_key()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
