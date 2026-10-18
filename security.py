"""
Bitetech Technologies — Core Application Security & Defensive Engineering Module.
Implements:
- Safe URL validation (prevent open redirects)
- In-memory thread-safe sliding window rate limiting
- Structured security audit logging (zero credentials logged)
- TOTP Multi-Factor Authentication (RFC 6238 via pyotp)
- Incident Response / Emergency Mode enforcement
- Input sanitization helpers
"""

import time
import logging
from collections import defaultdict
from threading import Lock
from urllib.parse import urlsplit
import pyotp
from flask import request, current_app
from extensions import db

# Configure private server-side security logger
security_logger = logging.getLogger('bitetech.security')
security_logger.setLevel(logging.INFO)
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[SECURITY] %(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)

# ---------------------------------------------------------------------------
# 1. Open Redirect Prevention
# ---------------------------------------------------------------------------
def is_safe_url(target):
    r"""
    Validate that target URL is relative and points to the same origin.
    Prevents open redirect attacks (e.g. //evil.com, \evil.com, javascript:).
    """
    if not target:
        return False

    # Block backslashes and protocol-relative attempts
    target_clean = target.strip()
    if target_clean.startswith('\\') or target_clean.startswith('//'):
        return False

    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(target_clean)

    # Must be relative or have matching host and scheme
    if test_url.scheme and test_url.scheme not in ('http', 'https'):
        return False

    if test_url.netloc and test_url.netloc != ref_url.netloc:
        return False

    # Disallow dangerous schemes like data:, javascript:
    if ':' in test_url.path and not (target_clean.startswith('/') or target_clean.startswith('.')):
        return False

    return True

# ---------------------------------------------------------------------------
# 2. Sliding Window Rate Limiter (Thread-safe)
# ---------------------------------------------------------------------------
class SlidingWindowRateLimiter:
    """
    In-memory thread-safe sliding window rate limiter.
    Limits requests per IP over a rolling time window.
    """
    def __init__(self):
        self._lock = Lock()
        self._requests = defaultdict(list)
        self._last_cleanup = time.time()

    def is_allowed(self, key, max_requests, window_seconds):
        now = time.time()
        with self._lock:
            # Periodic cleanup of expired entries
            if now - self._last_cleanup > 300:
                self._cleanup(now)

            window_start = now - window_seconds
            # Filter timestamps in current window
            valid_timestamps = [ts for ts in self._requests[key] if ts > window_start]
            
            if len(valid_timestamps) >= max_requests:
                self._requests[key] = valid_timestamps
                return False, int(window_seconds - (now - valid_timestamps[0])) + 1

            valid_timestamps.append(now)
            self._requests[key] = valid_timestamps
            return True, 0

    def _cleanup(self, now):
        cutoff = now - 3600
        keys_to_delete = []
        for key, timestamps in self._requests.items():
            active = [ts for ts in timestamps if ts > cutoff]
            if not active:
                keys_to_delete.append(key)
            else:
                self._requests[key] = active
        for k in keys_to_delete:
            del self._requests[k]
        self._last_cleanup = now

# Global rate limiter instances
limiter = SlidingWindowRateLimiter()

def get_client_ip():
    """Extract client IP address safely."""
    # Check X-Forwarded-For only if configured behind a trusted proxy
    trusted_proxies = current_app.config.get('TRUSTED_PROXIES', False) if current_app else False
    if trusted_proxies and request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return ip
    return request.remote_addr or '127.0.0.1'

# ---------------------------------------------------------------------------
# 3. Security Audit Logging (No passwords/tokens recorded)
# ---------------------------------------------------------------------------
def log_security_event(action, user=None, target_type=None, target_id=None, details=None, status='SUCCESS'):
    """
    Persist administrative actions and security events to database and log.
    Ensures zero credentials, tokens, or passwords are ever saved.
    """
    try:
        from models import AuditLog
        from datetime import datetime, timezone

        ip = get_client_ip()
        user_agent = (request.headers.get('User-Agent') or 'Unknown')[:250]
        
        user_id = user.id if user else None
        username = user.username if user else None

        # Sanitize details to guarantee no secrets leak into logs
        sanitized_details = str(details)[:1000] if details else None
        if sanitized_details:
            for sensitive_kw in ('password', 'secret', 'csrf', 'token', 'key'):
                if sensitive_kw in sanitized_details.lower():
                    sanitized_details = f"[REDACTED CONTENT - Contains sensitive keyword: {sensitive_kw}]"

        log_entry = AuditLog(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            username=username,
            action=action[:100],
            target_type=target_type[:50] if target_type else None,
            target_id=str(target_id)[:50] if target_id else None,
            details=sanitized_details,
            ip_address=ip[:45],
            user_agent=user_agent,
            status=status[:20]
        )
        db.session.add(log_entry)
        db.session.commit()

        security_logger.info(
            f"Event='{action}' Status='{status}' User='{username or 'Anonymous'}' IP='{ip}' Target='{target_type}:{target_id}'"
        )
    except Exception as e:
        # Fallback to standard logger so failure to audit log doesn't crash the application
        security_logger.error(f"Failed to record audit log: {str(e)}")

# ---------------------------------------------------------------------------
# 4. Multi-Factor Authentication (MFA / TOTP)
# ---------------------------------------------------------------------------
def generate_totp_secret():
    """Generate a random 32-character base32 secret for TOTP."""
    return pyotp.random_base32()

def get_totp_uri(secret, username, issuer_name="Bitetech Technologies"):
    """Generate the otpauth:// URI for authenticator apps (Google Authenticator, Authy)."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer_name)

def verify_totp_code(secret, code):
    """Verify a 6-digit TOTP code with standard drift allowance (+/- 1 interval)."""
    if not secret or not code:
        return False
    try:
        totp = pyotp.TOTP(secret)
        # valid_window=1 allows for +/- 30 seconds of clock drift
        return totp.verify(str(code).strip(), valid_window=1)
    except Exception as e:
        security_logger.warning(f"TOTP verification error: {str(e)}")
        return False

# ---------------------------------------------------------------------------
# 5. Incident Response & Lockdown Mode Helper
# ---------------------------------------------------------------------------
def get_incident_mode():
    """
    Check current incident mode from database site settings:
    - 'normal': Standard operations
    - 'read_only': Public submissions blocked for maintenance / mitigation
    - 'lockdown': Admin login disabled, all public submissions blocked
    """
    try:
        from models import SiteSetting
        return SiteSetting.get_setting('incident_mode', 'normal')
    except Exception:
        return 'normal'
