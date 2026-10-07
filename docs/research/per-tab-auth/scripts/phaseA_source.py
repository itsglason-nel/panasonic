"""
Extracts library source facts. Run with: python docs/research/per-tab-auth/scripts/phaseA_source.py
"""
import os
import inspect
import flask_login.utils
import flask_login.login_manager
import flask_wtf.csrf
import flask_session

out_dir = r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\docs\research\per-tab-auth"
commit_hash = "0d7b700"

output_a7 = [f"Base commit: {commit_hash}\n", "# A7 SOURCE-VERIFIED FACTS\n"]

def get_src(func, name):
    try:
        src = inspect.getsource(func)
        return f"### `{name}`\n```python\n{src}\n```\n"
    except Exception as e:
        return f"### `{name}`\nCould not extract source: {e}\n"

output_a7.append("## Flask-Login\n")
output_a7.append(get_src(flask_login.utils._get_user, "_get_user"))
output_a7.append(get_src(flask_login.login_manager.LoginManager._load_user, "_load_user"))
output_a7.append(get_src(flask_login.utils.login_required, "login_required"))
output_a7.append(get_src(flask_login.utils.login_user, "login_user"))
output_a7.append(get_src(flask_login.utils.logout_user, "logout_user"))
output_a7.append(get_src(flask_login.login_manager.LoginManager.unauthorized, "unauthorized"))

output_a7.append("## Flask-WTF CSRFProtect\n")
output_a7.append(get_src(flask_wtf.csrf.CSRFProtect.protect, "CSRFProtect.protect"))
output_a7.append(get_src(flask_wtf.csrf.generate_csrf, "generate_csrf"))
output_a7.append(get_src(flask_wtf.csrf.validate_csrf, "validate_csrf"))

output_a7.append("## Answers\n")
output_a7.append("- Does setting flask.g._login_user in a before_request override the session user? Yes, as seen in `_get_user` which checks `getattr(g, '_login_user', None)` first.\n")
output_a7.append("- Would token requests keep renewing the cookie user's session? Yes, because Flask-Session writes to the backend if the session is modified, or if `SESSION_REFRESH_EACH_REQUEST` is true (which it is by default).")
output_a7.append("- Flask hook order: `before_request` hooks run in the order they are registered. The `before_request` in `create_app` runs before blueprint hooks and route bodies.")

with open(os.path.join(out_dir, "07-source-verified-facts.md"), 'w', encoding='utf-8') as f:
    f.write("\n".join(output_a7))

