"""
PMPC Data Logger — Flask Application Factory
"""
import os
import logging
from flask import Flask
from flask_login import LoginManager
from flask_session import Session
from flask_socketio import SocketIO  # type: ignore
from flask_wtf.csrf import CSRFProtect
import redis

from config import config_map
from app.models import db

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Global extensions
login_manager = LoginManager()
session_ext = Session()
socketio = SocketIO()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates',
    )
    app.config.from_object(config_map[config_name])

    # ── Initialize extensions ──
    db.init_app(app)

    # Redis session
    try:
        redis_client = redis.Redis(
            host=app.config.get('REDIS_HOST', '127.0.0.1'),
            port=app.config.get('REDIS_PORT', 6379),
            socket_timeout=1, # Quick timeout for the fallback check
        )
        redis_client.ping() # Force connection attempt
        app.config['SESSION_REDIS'] = redis_client
    except Exception:
        # Fallback to filesystem sessions if Redis is not available
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = os.path.join(
            os.path.dirname(__file__), '.flask_sessions'
        )
    session_ext.init_app(app)

    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Flask-SocketIO
    cors_origins = app.config.get('CORS_ALLOWED_ORIGINS', 'http://127.0.0.1:8080')
    socketio.init_app(app, async_mode='eventlet', cors_allowed_origins=cors_origins)

    # ── Register blueprints ──
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    # CSRF protection — exempt JSON API blueprints (they use session auth + same-origin)
    csrf.init_app(app)
    csrf.exempt(api_bp)
    csrf.exempt(admin_bp)

    # ── Security headers & cache control ────────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'

        # Cache-control for HTML pages — prevent browser from caching authenticated pages
        if response.content_type and 'text/html' in response.content_type:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        return response

    # ── Error Handlers ─────────────────────────────────────────────────────────
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error_code='404', error_title='Not Found', error_desc='The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('error.html', error_code='403', error_title='Forbidden', error_desc="You don't have the permission to access the requested resource. It is either read-protected or not readable by the server."), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html', error_code='500', error_title='Internal Server Error', error_desc='The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.'), 500

    # ── Auto-close previous days' work schedules ───────────────────────────────
    @app.before_request
    def auto_close_previous_days():
        """Finalize all worksched rows from before today on the first request of each day.

        Uses Redis (if available) and system_state table to track whether we've already run today,
        so we only execute the UPDATE once per calendar day (not every request).
        """
        from datetime import date
        from sqlalchemy import text
        from flask import request as flask_request
        from flask import current_app

        # Only run on routes that touch the DB (skip static files)
        if flask_request.endpoint == 'static':
            return

        today_str = str(date.today())
        redis_client = current_app.config.get('SESSION_REDIS')
        redis_key = 'pmpc:last_autoclose_date'

        # Fast path: Check Redis first to avoid DB roundtrip on every request
        if redis_client:
            try:
                if redis_client.get(redis_key) == today_str.encode('utf-8') or redis_client.get(redis_key) == today_str:
                    return # Already ran today - skip
            except Exception:
                pass # Fallback to DB if Redis fails

        try:
            row = db.session.execute(
                text("SELECT value FROM system_state WHERE key_name = 'last_autoclose_date'")
            ).fetchone()

            if row and row[0] == today_str:
                # Update Redis so subsequent requests are fast
                if redis_client:
                    try:
                        redis_client.set(redis_key, today_str, ex=86400)
                    except Exception:
                        pass
                return  # Already ran today — skip

            # Finalize all previous unfinished days
            db.session.execute(text("""
                UPDATE worksched
                SET    finalized    = 1,
                       finalized_at = NOW(),
                       finalized_by = 'system'
                WHERE  date      < :today
                  AND  finalized = 0
            """), {'today': today_str})

            # Record that we've run today
            db.session.execute(text("""
                UPDATE system_state
                SET    value = :today
                WHERE  key_name = 'last_autoclose_date'
            """), {'today': today_str})

            db.session.commit()

            # Update Redis cache
            if redis_client:
                try:
                    redis_client.set(redis_key, today_str, ex=86400)
                except Exception:
                    pass

        except Exception as e:
            # Never crash the app if this fails
            db.session.rollback()
            logger.warning('auto_close_previous_days failed: %s', e)

    # ── Create tables (dev only) ──
    with app.app_context():
        if app.config.get('DEBUG'):
            db.create_all()
            logger.info('db.create_all() completed (development mode only).')

    logger.info('PMPC Data Logger started in "%s" mode.', config_name)
    return app

