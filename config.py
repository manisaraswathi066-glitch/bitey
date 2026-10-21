import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project root
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

class Config:
    """Base configuration with sensible defaults."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bitetech-super-secret-production-safe-key-2026-v1')
    
    # Detect serverless environment (e.g. Vercel)
    IS_VERCEL = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'))
    
    # Database Configuration:
    # Defaults to SQLite development DB if DATABASE_URL is not set or USE_SQLITE is explicitly set
    USE_SQLITE = os.environ.get('USE_SQLITE', 'True').lower() in ('true', '1', 't', 'yes')
    
    # WAMP MySQL Default: mysql+pymysql://root:@localhost:3306/bitetech_db
    MYSQL_USER = os.environ.get('DB_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD', '')
    MYSQL_HOST = os.environ.get('DB_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('DB_PORT', '3306')
    MYSQL_NAME = os.environ.get('DB_NAME', 'bitetech_db')
    
    mysql_uri = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_NAME}?charset=utf8mb4"
    
    # On Vercel serverless, the filesystem outside the OS temp dir is read-only
    if IS_VERCEL:
        import tempfile
        tmp_db_path = (Path(tempfile.gettempdir()) / 'bitetech.db').as_posix()
        sqlite_uri = f"sqlite:///{tmp_db_path}"
    else:
        sqlite_uri = f"sqlite:///{(basedir / 'instance' / 'bitetech.db').as_posix()}"
    
    raw_db_url = os.environ.get('DATABASE_URL')
    if raw_db_url:
        if raw_db_url.startswith("postgres://"):
            raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = raw_db_url
    elif not USE_SQLITE and not IS_VERCEL:
        SQLALCHEMY_DATABASE_URI = mysql_uri
    else:
        SQLALCHEMY_DATABASE_URI = sqlite_uri
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # Security & Sessions
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')
    PERMANENT_SESSION_LIFETIME = 3600 * 4  # 4 hours
    
    # WTForms / CSRF & Payload Size Limits
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600 * 2
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max payload limit
    
    # Pagination
    ITEMS_PER_PAGE = 9
    ADMIN_ITEMS_PER_PAGE = 15

    # Company Contact defaults
    COMPANY_NAME = "Bitetech Technologies"
    COMPANY_EMAIL = "bitetechtechnologies@gmail.com"
    COMPANY_PHONE = "7418332912"
    WHATSAPP_NUMBER = "917418332912"
    STARTING_PRICE = 599

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
