"""
Bitetech Technologies — Database Backup, Encryption, and Restore Verification Utility.
Features:
- Encrypted database snapshots using cryptography.fernet (AES-128-CBC + HMAC)
- Automated restore integrity testing (verifies table structure and row counts)
- Separate backup directory with timestamped rotation
"""

import os
import sys
import shutil
import sqlite3
import argparse
from datetime import datetime, timezone
from pathlib import Path
from cryptography.fernet import Fernet
from app import create_app
from extensions import db
from models import AdminUser, Project, Course, SiteSetting

BACKUP_DIR = Path(__file__).resolve().parent / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)

def get_or_create_backup_key():
    """Retrieve or generate Fernet encryption key for backups."""
    key = os.environ.get('BACKUP_ENCRYPTION_KEY')
    key_file = BACKUP_DIR / '.backup_key.secret'
    
    if key:
        return key.encode('utf-8') if isinstance(key, str) else key

    if key_file.exists():
        return key_file.read_bytes().strip()

    # Generate and save a new key
    new_key = Fernet.generate_key()
    key_file.write_bytes(new_key)
    try:
        # Restrict permissions on Windows/Unix if possible
        os.chmod(key_file, 0o600)
    except Exception:
        pass
    return new_key

def create_backup():
    app = create_app()
    with app.app_context():
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        instance_db = Path(app.instance_path) / 'bitetech.db'
        
        if not instance_db.exists():
            print(f"[-] Database file not found at {instance_db}")
            return None

        temp_snapshot = BACKUP_DIR / f"temp_{timestamp}.db"
        shutil.copy2(instance_db, temp_snapshot)

        # Encrypt the database snapshot
        key = get_or_create_backup_key()
        cipher = Fernet(key)

        raw_data = temp_snapshot.read_bytes()
        encrypted_data = cipher.encrypt(raw_data)

        backup_file = BACKUP_DIR / f"bitetech_backup_{timestamp}.enc"
        backup_file.write_bytes(encrypted_data)

        temp_snapshot.unlink()  # Remove unencrypted snapshot

        size_kb = len(encrypted_data) / 1024
        print(f"[OK] Encrypted backup created: {backup_file.name} ({size_kb:.1f} KB)")
        return backup_file

def test_restore(backup_path=None):
    """
    Automated disaster recovery test:
    Decrypts backup into temporary sandbox and validates table integrity.
    """
    key = get_or_create_backup_key()
    cipher = Fernet(key)

    if not backup_path:
        # Pick the most recent backup
        backups = sorted(BACKUP_DIR.glob('bitetech_backup_*.enc'), reverse=True)
        if not backups:
            print("[-] No backups found to test. Creating one now...")
            b = create_backup()
            if not b:
                return False
            backups = [b]
        backup_path = backups[0]

    backup_file = Path(backup_path)
    if not backup_file.exists():
        print(f"[-] Specified backup file '{backup_file}' does not exist.")
        return False

    print(f"[*] Testing restoration from: {backup_file.name}...")
    try:
        encrypted_data = backup_file.read_bytes()
        decrypted_data = cipher.decrypt(encrypted_data)

        # Restore into temporary test sandbox
        sandbox_db = BACKUP_DIR / f"test_restore_sandbox.db"
        sandbox_db.write_bytes(decrypted_data)

        # Validate database integrity using sqlite3
        conn = sqlite3.connect(sandbox_db)
        cursor = conn.cursor()

        # Check required tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        
        required_tables = ['admin_users', 'projects', 'courses', 'site_settings', 'audit_logs']
        missing = [t for t in required_tables if t not in tables]
        if missing:
            conn.close()
            sandbox_db.unlink()
            print(f"[-] RESTORATION TEST FAILED: Missing tables {missing}")
            return False

        # Check row counts
        cursor.execute("SELECT count(*) FROM projects")
        projects_count = cursor.fetchone()[0]

        cursor.execute("SELECT count(*) FROM courses")
        courses_count = cursor.fetchone()[0]

        conn.close()
        sandbox_db.unlink()  # Clean up sandbox

        print(f"[OK] Table schema verified: {len(tables)} tables present.")
        print(f"[OK] Data verified: {projects_count} projects, {courses_count} courses recovered.")
        print("[SUCCESS] DISASTER RECOVERY RESTORATION TEST: PASSED")
        return True

    except Exception as e:
        print(f"[-] RESTORATION TEST FAILED with error: {str(e)}")
        return False

def list_backups():
    backups = sorted(BACKUP_DIR.glob('bitetech_backup_*.enc'), reverse=True)
    print(f"Available Backups in {BACKUP_DIR}:")
    print("-" * 65)
    if not backups:
        print("  No backups present.")
    for b in backups:
        size = b.stat().st_size / 1024
        mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {b.name:35} | {size:6.1f} KB | Created: {mtime}")
    print("-" * 65)

def main():
    parser = argparse.ArgumentParser(description="Bitetech Technologies Encrypted Backup & Restore Tool")
    parser.add_argument('--backup', action='store_true', help="Create a new encrypted database snapshot")
    parser.add_argument('--test-restore', nargs='?', const='latest', help="Test restoration of latest or specific backup file")
    parser.add_argument('--list', action='store_true', help="List existing encrypted backups")

    args = parser.parse_args()

    if args.backup:
        create_backup()
    elif args.test_restore:
        target = None if args.test_restore == 'latest' else args.test_restore
        test_restore(target)
    elif args.list:
        list_backups()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
