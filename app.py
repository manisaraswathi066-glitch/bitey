import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, Response
from flask_wtf.csrf import CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix
from config import config_by_name
from extensions import db, csrf, login_manager, migrate
from routes import main_bp, admin_bp
from models import SiteSetting, User

# Security logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('bitetech')

class VercelPathFixMiddleware:
    """
    Ensures Vercel edge rewrite paths correctly match Flask endpoints:
    1. Extracts real path from HTTP_X_MATCHED_PATH, REQUEST_URI, or PATH_INFO.
    2. Maps /api/index.py, /api/index, or /api directly to the root /.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched = environ.get('HTTP_X_MATCHED_PATH')
        req_uri = environ.get('REQUEST_URI') or environ.get('RAW_URI')
        
        if matched and matched not in ('/api/index.py', '/api/index', '/api'):
            environ['PATH_INFO'] = matched
        elif req_uri:
            from urllib.parse import urlparse
            parsed_path = urlparse(req_uri).path
            if parsed_path not in ('/api/index.py', '/api/index', '/api'):
                environ['PATH_INFO'] = parsed_path
            else:
                environ['PATH_INFO'] = '/'
        elif environ.get('PATH_INFO') in ('/api/index.py', '/api/index', '/api'):
            environ['PATH_INFO'] = '/'
            
        return self.wsgi_app(environ, start_response)

def create_app(config_name=None):
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')
        
    app = Flask(__name__)
    cfg = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(cfg)

    # Defensive Check: Warn or enforce against weak default secret keys in production
    secret_key = app.config.get('SECRET_KEY', '')
    if 'dev-key' in secret_key or len(secret_key) < 24:
        if config_name == 'production':
            if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
                import secrets
                app.config['SECRET_KEY'] = secrets.token_hex(32)
                logger.warning("[SECURITY ADVISORY] Generated fallback SECRET_KEY for Vercel serverless environment.")
            else:
                logger.warning("[SECURITY ADVISORY] Running with default SECRET_KEY in production. Configure a strong random key in .env.")
        else:
            logger.warning("[SECURITY ADVISORY] Running with development SECRET_KEY. Configure a strong random key in .env for production.")
    
    # Ensure instance folder exists for SQLite fallback (safely catch on read-only environments like Vercel)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Vercel Serverless: copy seed_data.db to temporary database on cold start if needed
    is_vercel = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'))
    if is_vercel:
        try:
            import shutil
            import tempfile
            from pathlib import Path
            base_dir = Path(__file__).resolve().parent
            seed_file = base_dir / 'seed_data.db'
            tmp_db = Path(tempfile.gettempdir()) / 'bitetech.db'
            if seed_file.exists() and (not tmp_db.exists() or tmp_db.stat().st_size == 0):
                shutil.copy2(seed_file, tmp_db)
                logger.info(f"[DB] Copied seed_data.db to {tmp_db} successfully.")
        except Exception as e:
            logger.warning(f"[DB] Could not copy seed_data.db to temp directory: {e}")
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = "Please sign in to access your personal dashboard."
    login_manager.login_message_category = "info"
    migrate.init_app(app, db)

    # Defensive check: ensure database tables exist (e.g. fresh Vercel /tmp container)
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if not inspector.has_table('projects') or not inspector.has_table('users'):
                logger.info("[DB AUTO-INIT] Missing tables detected. Running db.create_all()...")
                db.create_all()
                try:
                    from init_db import init_database
                    init_database(seed_demo=True)
                except Exception as seed_err:
                    logger.warning(f"[DB AUTO-INIT] Seeding note: {seed_err}")
        except Exception as inspect_err:
            logger.warning(f"[DB AUTO-INIT] Inspection note: {inspect_err}")

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None
    
    # Reverse Proxy Support: Safely interpret X-Forwarded headers when behind reverse proxy
    if os.environ.get('BEHIND_REVERSE_PROXY', 'False').lower() in ('true', '1'):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Static file serving via WhiteNoise (Vercel serverless fallback & high-performance edge streaming)
    try:
        from whitenoise import WhiteNoise
        base_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(base_dir, 'static')
        if not os.path.exists(static_dir):
            static_dir = os.path.join(base_dir, 'public', 'static')
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_dir, prefix='static/')
    except Exception as e:
        logger.warning(f"[STATIC] WhiteNoise setup notice: {e}")
    
    # Vercel Serverless Path Normalization Middleware
    app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # Global template context processor
    @app.context_processor
    def inject_global_settings():
        company_name = SiteSetting.get_setting('company_name', app.config.get('COMPANY_NAME', 'Bitetech Technologies'))
        company_email = SiteSetting.get_setting('company_email', app.config.get('COMPANY_EMAIL', 'bitetechtechnologies@gmail.com'))
        company_phone = SiteSetting.get_setting('company_phone', app.config.get('COMPANY_PHONE', '7418332912'))
        whatsapp_number = SiteSetting.get_setting('whatsapp_number', app.config.get('WHATSAPP_NUMBER', '917418332912'))
        starting_price = SiteSetting.get_setting('starting_price', str(app.config.get('STARTING_PRICE', 599)))
        hero_headline = SiteSetting.get_setting('hero_headline', 'Turning Python Ideas into Working Projects.')
        incident_mode = SiteSetting.get_setting('incident_mode', 'normal')
        
        return {
            'site_settings': {
                'company_name': company_name,
                'company_email': company_email,
                'company_phone': company_phone,
                'whatsapp_number': whatsapp_number,
                'starting_price': starting_price,
                'hero_headline': hero_headline,
                'incident_mode': incident_mode
            },
            'current_year': datetime.now().year
        }

    # ---------------------------------------------------------------------------
    # HTTP Security Headers Middleware (OWASP Defense-in-Depth)
    # ---------------------------------------------------------------------------
    @app.after_request
    def set_security_headers(response: Response):
        # 1. Content Security Policy (CSP)
        # Tailored for self, Bootstrap CDN, Google Fonts, and Font Awesome/Bootstrap Icons
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self' https://wa.me;"
        )
        response.headers['Content-Security-Policy'] = csp_policy

        # 2. Prevent MIME-sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # 3. Clickjacking Protection
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'

        # 4. Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # 5. Restrict Unneeded Browser Permissions
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=()'

        # 6. HSTS (Strict-Transport-Security) in HTTPS Production
        if app.config.get('SESSION_COOKIE_SECURE', False) or request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        # 7. Cache-control for sensitive admin routes
        if request.path.startswith('/admin'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'

        return response
        
    # ---------------------------------------------------------------------------
    # Generic, Secure Error Handlers (Zero stack traces / internal paths leaked)
    # ---------------------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('404.html', title="Bad Request (400)", message="The request could not be understood or contained invalid parameters."), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('404.html', title="Access Denied (403)", message="You do not have administrative authorization to view this resource."), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html', title="Page Not Found (404)", message="The requested page could not be located on this server."), 404

    @app.errorhandler(429)
    def rate_limit_error(error):
        return render_template('404.html', title="Too Many Requests (429)", message="Rate limit exceeded. Please pause briefly before submitting additional requests."), 429

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"Internal server error: {str(error)}")
        return render_template('500.html'), 500

    @app.errorhandler(503)
    def service_unavailable_error(error):
        return render_template('404.html', title="Service Unavailable (503)", message="This platform is currently undergoing scheduled maintenance or defensive security operations. Please try again shortly."), 503

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('csrf_error.html', reason="Your session verification token has expired or is invalid. Please refresh the page and try submitting your request again."), 400

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
    app.run(host='127.0.0.1', port=port, debug=debug)
