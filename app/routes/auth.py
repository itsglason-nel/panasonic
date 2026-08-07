import logging
import time
from collections import defaultdict
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# ── Brute-force protection ────────────────────────────────────────────────────
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes
_login_attempts = defaultdict(list)  # IP → [timestamp, ...]


def _is_locked_out(ip):
    """Check if IP is locked out. Also prune old entries."""
    now = time.time()
    # Keep only attempts within the lockout window
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < LOCKOUT_SECONDS]
    return len(_login_attempts[ip]) >= MAX_ATTEMPTS


def _record_failed_attempt(ip):
    """Record a failed login attempt for the given IP."""
    _login_attempts[ip].append(time.time())


def _clear_attempts(ip):
    """Clear all failed attempts for the given IP on successful login."""
    _login_attempts.pop(ip, None)


def _get_remaining_lockout(ip):
    """Return remaining lockout time in seconds."""
    if not _login_attempts[ip]:
        return 0
    oldest_in_window = _login_attempts[ip][0]
    remaining = LOCKOUT_SECONDS - (time.time() - oldest_in_window)
    return max(0, int(remaining))


@auth_bp.route('/', methods=['GET'])
def index():
    """Root URL → login page (or redirect if already logged in)."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.admin_page'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    """Login page — username + password only, always lands on /admin."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.admin_page'))

    if request.method == 'POST':
        # CSRF validation
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception:
            abort(400, description='Invalid or missing CSRF token.')

        client_ip = request.remote_addr

        # Brute-force check
        if _is_locked_out(client_ip):
            remaining = _get_remaining_lockout(client_ip)
            minutes = remaining // 60
            seconds = remaining % 60
            flash(
                f'Too many failed attempts. Try again in {minutes}m {seconds}s.',
                'danger'
            )
            return render_template('login.html')

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username, is_active=True).first()

        if user and user.check_password(password):
            _clear_attempts(client_ip)
            login_user(user)
            session['selected_module'] = 'Administrator'

            if user.must_change_password:
                flash(
                    'Your account is using a default password. '
                    'Please contact the Super Administrator to reset it.',
                    'warning'
                )

            return redirect(url_for('admin.admin_page'))
        else:
            _record_failed_attempt(client_ip)
            attempts_left = MAX_ATTEMPTS - len(_login_attempts[client_ip])
            if attempts_left > 0:
                logger.warning('Failed login attempt for username "%s" from %s (%d attempts left)', username, client_ip, attempts_left)
                flash('Invalid username or password.', 'danger')
            else:
                logger.warning('IP %s locked out after %d failed attempts', client_ip, MAX_ATTEMPTS)
                remaining = _get_remaining_lockout(client_ip)
                minutes = remaining // 60
                seconds = remaining % 60
                flash(
                    f'Too many failed attempts. Try again in {minutes}m {seconds}s.',
                    'danger'
                )

    return render_template('login.html')

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Legacy redirect — always goes to admin now."""
    return redirect(url_for('admin.admin_page'))

@auth_bp.route('/auth/logout')
@login_required
def logout():
    """Clear session and redirect to login."""
    logout_user()
    session.pop('selected_module', None)
    session.pop('_flashes', None)
    return redirect(url_for('auth.login'))

@auth_bp.route('/auth/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    new_password = data.get('new_password')
    
    if not new_password or len(new_password) < 4:
        return jsonify({'success': False, 'message': 'Password must be at least 4 characters long.'}), 400
        
    current_user.set_password(new_password)
    current_user.must_change_password = False
    
    from app.models import db
    db.session.commit()
    
    try:
        from app.models.audit import log_audit
        log_audit(getattr(current_user, 'username', 'system'), 'UPDATE', 'users', current_user.id, {'action': 'changed_password'})
    except Exception:
        pass
    
    return jsonify({'success': True, 'message': 'Password changed successfully.'})
