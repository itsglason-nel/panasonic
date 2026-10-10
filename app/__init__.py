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


def parse_bool_env(var_name, default_val):
    val = os.environ.get(var_name, '').strip().lower()
    if val in ('1', 'true', 'yes', 'on'):
        return True
    elif val in ('0', 'false', 'no', 'off'):
        return False
    return default_val

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

    app.config['ENABLE_TAB_SESSIONS'] = parse_bool_env('ENABLE_TAB_SESSIONS', False)
    if app.config.get('ENABLE_TAB_SESSIONS', False):
        app.config['SESSION_COOKIE_NAME'] = 'pmpc_tab_session'
        app.config['SESSION_FILE_THRESHOLD'] = 5000
        
        from app.tabscope import register_prefix_policy
        register_prefix_policy(app)
    
    # ── Custom Config Flags ──
    app.config['HARDEN_API_CACHE'] = parse_bool_env('HARDEN_API_CACHE', True)
    require_https = parse_bool_env('REQUIRE_HTTPS', False)
    
    app.config['SESSION_COOKIE_SECURE'] = require_https
    app.config['REMEMBER_COOKIE_SECURE'] = require_https
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'

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

    if app.config.get('ENABLE_TAB_SESSIONS', False):
        from app.tabscope import apply_cookie_path
        apply_cookie_path(app)

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
    cors_origins = app.config.get('CORS_ALLOWED_ORIGINS', '*')
    if ',' in cors_origins:
        cors_origins = [origin.strip() for origin in cors_origins.split(',')]
    socketio.init_app(app, async_mode='eventlet', cors_allowed_origins=cors_origins)

    # ── Register blueprints ──
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp
    from app.routes.scoreboard import scoreboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(scoreboard_bp)

    # CSRF protection — exempt JSON API blueprints (they use session auth + same-origin)
    csrf.init_app(app)
    csrf.exempt(api_bp)
    csrf.exempt(admin_bp)
    csrf.exempt(scoreboard_bp)

    # ── Security headers & cache control ────────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        from flask import request
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'

        # Skip Cache-Control/Vary modifications for static files
        if request.endpoint == 'static':
            return response
            
        from flask import current_app
        harden_api = current_app.config.get('HARDEN_API_CACHE', True)

        # Cache-control for HTML and JSON pages — prevent browser from caching authenticated pages
        is_html = response.content_type and 'text/html' in response.content_type
        is_json = response.content_type and 'application/json' in response.content_type
        
        if is_html or (is_json and harden_api):
            response.headers.setdefault('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            response.headers.setdefault('Pragma', 'no-cache')
            response.headers.setdefault('Expires', '0')
            
            vary = response.headers.get('Vary', '')
            if 'Cookie' not in vary:
                response.headers['Vary'] = f"{vary}, Cookie" if vary else "Cookie"

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

    from flask_wtf.csrf import CSRFError
    from flask import redirect, url_for, flash, request as flask_request
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.warning(f"CSRF Error: {e.description} on {flask_request.url}")
        flash('Your session has expired or is invalid. Please try again.', 'error')
        # If user is logging in, redirect back to login
        if flask_request.endpoint == 'auth.login':
            return redirect(url_for('auth.login'))
        return redirect(flask_request.referrer or url_for('auth.login'))

    # ── Auto-close previous days' work schedules ───────────────────────────────
    @app.before_request
    def auto_close_previous_days():
        """Finalize all worksched rows from before the current production date on the first request of each day.

        Uses Redis (if available) and system_state table to track whether we've already run today.
        Respects overnight shifts (if current time is before an overnight shift's end_time, it is still "yesterday's" production day).
        """
        from datetime import date, datetime, timedelta
        from sqlalchemy import text
        from flask import request as flask_request
        from flask import current_app
        
        # Only run on routes that touch the DB (skip static files)
        if flask_request.endpoint == 'static':
            return

        now = datetime.now()
        current_date = now.date()
        production_date = current_date

        try:
            from app.models.shift import Shift
            overnight_shift = Shift.query.filter(Shift.end_time < Shift.start_time).first()
            if overnight_shift:
                # If we are before the end time of the overnight shift, we are technically still in "yesterday's" production day.
                if now.time() < overnight_shift.end_time:
                    production_date = current_date - timedelta(days=1)
        except Exception:
            pass # DB or table might not be initialized yet

        prod_date_str = str(production_date)
        redis_client = current_app.config.get('SESSION_REDIS')
        redis_key = 'pmpc:last_autoclose_date'

        # Fast path: Check Redis first to avoid DB roundtrip on every request
        if redis_client:
            try:
                if redis_client.get(redis_key) == prod_date_str.encode('utf-8') or redis_client.get(redis_key) == prod_date_str:
                    return # Already ran for this production date - skip
            except Exception:
                pass # Fallback to DB if Redis fails

        try:
            row = db.session.execute(
                text("SELECT value FROM system_state WHERE key_name = 'last_autoclose_date'")
            ).fetchone()

            if row and row[0] == prod_date_str:
                # Update Redis so subsequent requests are fast
                if redis_client:
                    try:
                        redis_client.set(redis_key, prod_date_str, ex=86400)
                    except Exception:
                        pass
                return  # Already ran for this production date — skip

            # Finalize all previous unfinished days (before the logical production date)
            db.session.execute(text("""
                UPDATE worksched
                SET    finalized    = 1,
                       finalized_at = NOW(),
                       finalized_by = 'system'
                WHERE  date      < :prod_date
                  AND  finalized = 0
            """), {'prod_date': prod_date_str})

            # Clean stale linestat: if active_date is old AND all station vars are 0,
            # reset to 'No Work'. If vars > 0, leave it for WIP resolution.
            db.session.execute(text("""
                UPDATE linestat
                SET    status = 'No Work',
                       active_date = NULL,
                       crsmodelcode = NULL, crsvar = 0,
                       attmodelcode = NULL, attvar = 0,
                       gmsmodelcode = NULL, gmsvar = 0,
                       inmodelcode = NULL, invar = 0,
                       inunique = NULL,
                       inpart1mod = NULL, inpart1desc = NULL,
                       inpart2mod = NULL, inpart2desc = NULL,
                       inpart3mod = NULL, inpart3desc = NULL,
                       inpart4mod = NULL, inpart4desc = NULL,
                       inpart5mod = NULL, inpart5desc = NULL,
                       inpart6mod = NULL, inpart6desc = NULL,
                       outmodelcode = NULL, outvar = 0,
                       outmodel = NULL,
                       outpart1mod = NULL, outpart1desc = NULL,
                       outpart2mod = NULL, outpart2desc = NULL,
                       outpart3mod = NULL, outpart3desc = NULL,
                       gascharge = 0,
                       compmod = NULL, fan1mod = NULL, fan2mod = NULL,
                       crspart1mod = NULL, crspart1desc = NULL,
                       crspart2mod = NULL, crspart2desc = NULL,
                       crspart3mod = NULL, crspart3desc = NULL,
                       crspart4mod = NULL, crspart4desc = NULL,
                       area = NULL, serialstart = NULL,
                       updtime = NOW()
                WHERE  active_date < :prod_date
                  AND  (crsvar IS NULL OR crsvar = 0)
                  AND  (attvar IS NULL OR attvar = 0)
                  AND  (gmsvar IS NULL OR gmsvar = 0)
                  AND  (invar IS NULL OR invar = 0)
                  AND  (outvar IS NULL OR outvar = 0)
            """), {'prod_date': prod_date_str})

            # Record that we've run for this production date
            db.session.execute(text("""
                UPDATE system_state
                SET    value = :prod_date
                WHERE  key_name = 'last_autoclose_date'
            """), {'prod_date': prod_date_str})

            db.session.commit()

            # Update Redis cache
            if redis_client:
                try:
                    redis_client.set(redis_key, prod_date_str, ex=86400)
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

        # ── PLC restart notification ───────────────────────────────────────────
        # Stamp updtime = NOW() on every application startup so the PLC detects
        # the change and re-requests linestat data. The PLC is directly wired to
        # this PC; on shutdown/restart it loses all cached linestat values and
        # relies on an advancing updtime to know it must resync.
        # This runs unconditionally (bypasses the auto_close_previous_days gate
        # which only fires once per calendar day and would miss same-day restarts).
        try:
            from sqlalchemy import text as _startup_text
            db.session.execute(_startup_text("UPDATE linestat SET updtime = NOW()"))
            db.session.commit()
            logger.info('linestat.updtime stamped on startup — PLC will resync data.')
        except Exception as _startup_err:
            db.session.rollback()
            logger.warning('Startup linestat updtime bump failed (DB may not be ready): %s', _startup_err)

    # ── Start Background Workers ──────────────────────────────────────────────
    try:
        from app.services.pdf_observer import start_pdf_observer
        start_pdf_observer(app)
    except Exception as e:
        logger.warning('Failed to start PDF observer thread: %s', e)
        
    try:
        from app.services.transfer_slip_observer import start_transfer_slip_observer
        start_transfer_slip_observer(app)
    except Exception as e:
        logger.warning('Failed to start Transfer Slip observer thread: %s', e)

    try:
        from app.services.model_import_observer import start_model_import_observer
        start_model_import_observer(app)
    except Exception as e:
        logger.warning('Failed to start Model Import observer thread: %s', e)

    logger.info('PMPC Data Logger started in "%s" mode.', config_name)
    if app.config.get('ENABLE_TAB_SESSIONS', False):
        from app.tabscope import TabScope
        app.wsgi_app = TabScope(app.wsgi_app)
    return app

