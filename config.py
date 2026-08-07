"""
PMPC Data Logger — Application Configuration
Panasonic Manufacturing Philippines Corporation
"""
import os
from dotenv import load_dotenv

load_dotenv()



class Config:
    """Base configuration."""

    # Flask
    # SECRET_KEY must be set via environment variable. Raise on startup if missing.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. "
            "Generate one with: py -c \"import secrets; print(secrets.token_hex(32))\""
        )
    DEBUG = False
    TESTING = False

    # Database — MySQL 8.x via PyMySQL
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'plcdata')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # Redis — Session storage
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'pmpc_session:'
    REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

    # Flask-Login
    LOGIN_DISABLED = False
    REMEMBER_COOKIE_DURATION = 86400  # 24 hours

    # Session cookie hardening
    SESSION_COOKIE_HTTPONLY = True       # JS cannot read the session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'     # Prevents CSRF via cross-site requests
    SESSION_COOKIE_NAME = 'pmpc_session'  # Non-guessable cookie name

    # SocketIO CORS — set to the server's LAN address in production
    CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://127.0.0.1:8080')

    # Serial Port — Weighing Indicator (Instru-Tech FI05-150K-4252C)
    SERIAL_PORT = os.environ.get('SERIAL_PORT', 'COM3')
    SERIAL_BAUDRATE = int(os.environ.get('SERIAL_BAUDRATE', 9600))
    SERIAL_TIMEOUT = float(os.environ.get('SERIAL_TIMEOUT', 1.0))

    # Server
    SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 8080))

    # Gas charge tolerance (kg) — from instrument specification d=0.005 kg
    GAS_CHARGE_TOLERANCE_KG = float(os.environ.get('GAS_CHARGE_TOLERANCE_KG', 0.020))

    # Backup
    BACKUP_DIR = os.environ.get('BACKUP_DIR', os.path.join(os.path.dirname(__file__), 'backups'))

    # BOM import source
    BOM_EXCEL_PATH = os.environ.get(
        'BOM_EXCEL_PATH',
        os.path.join(os.path.dirname(__file__), 'DATA FROM DATA LOGGER.xlsx')
    )


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration — LAN deployment on 192.168.1.100."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration map
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
