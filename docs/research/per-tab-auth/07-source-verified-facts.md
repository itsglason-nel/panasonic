Base commit: 0d7b700

# A7 SOURCE-VERIFIED FACTS

## Flask-Login

### `_get_user`
```python
def _get_user():
    if has_request_context():
        if "_login_user" not in g:
            current_app.login_manager._load_user()

        return g._login_user

    return None

```

### `_load_user`
```python
    def _load_user(self):
        """Loads user from session or remember_me cookie as applicable"""

        if self._user_callback is None and self._request_callback is None:
            raise Exception(
                "Missing user_loader or request_loader. Refer to "
                "http://flask-login.readthedocs.io/#how-it-works "
                "for more info."
            )

        user_accessed.send(current_app._get_current_object())

        # Check SESSION_PROTECTION
        if self._session_protection_failed():
            return self._update_request_context_with_user()

        user = None

        # Load user from Flask Session
        user_id = session.get("_user_id")
        if user_id is not None and self._user_callback is not None:
            user = self._user_callback(user_id)

        # Load user from Remember Me Cookie or Request Loader
        if user is None:
            config = current_app.config
            cookie_name = config.get("REMEMBER_COOKIE_NAME", COOKIE_NAME)
            header_name = config.get("AUTH_HEADER_NAME", AUTH_HEADER_NAME)
            has_cookie = (
                cookie_name in request.cookies and session.get("_remember") != "clear"
            )
            if has_cookie:
                cookie = request.cookies[cookie_name]
                user = self._load_user_from_remember_cookie(cookie)
            elif self._request_callback:
                user = self._load_user_from_request(request)
            elif header_name in request.headers:
                header = request.headers[header_name]
                user = self._load_user_from_header(header)

        return self._update_request_context_with_user(user)

```

### `login_required`
```python
def login_required(func):
    """
    If you decorate a view with this, it will ensure that the current user is
    logged in and authenticated before calling the actual view. (If they are
    not, it calls the :attr:`LoginManager.unauthorized` callback.) For
    example::

        @app.route('/post')
        @login_required
        def post():
            pass

    If there are only certain times you need to require that your user is
    logged in, you can do so with::

        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()

    ...which is essentially the code that this function adds to your views.

    It can be convenient to globally turn off authentication when unit testing.
    To enable this, if the application configuration variable `LOGIN_DISABLED`
    is set to `True`, this decorator will be ignored.

    .. Note ::

        Per `W3 guidelines for CORS preflight requests
        <http://www.w3.org/TR/cors/#cross-origin-request-with-preflight-0>`_,
        HTTP ``OPTIONS`` requests are exempt from login checks.

    :param func: The view function to decorate.
    :type func: function
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in EXEMPT_METHODS or current_app.config.get("LOGIN_DISABLED"):
            pass
        elif not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()

        # flask 1.x compatibility
        # current_app.ensure_sync is only available in Flask >= 2.0
        if callable(getattr(current_app, "ensure_sync", None)):
            return current_app.ensure_sync(func)(*args, **kwargs)
        return func(*args, **kwargs)

    return decorated_view

```

### `login_user`
```python
def login_user(user, remember=False, duration=None, force=False, fresh=True):
    """
    Logs a user in. You should pass the actual user object to this. If the
    user's `is_active` property is ``False``, they will not be logged in
    unless `force` is ``True``.

    This will return ``True`` if the log in attempt succeeds, and ``False`` if
    it fails (i.e. because the user is inactive).

    :param user: The user object to log in.
    :type user: object
    :param remember: Whether to remember the user after their session expires.
        Defaults to ``False``.
    :type remember: bool
    :param duration: The amount of time before the remember cookie expires. If
        ``None`` the value set in the settings is used. Defaults to ``None``.
    :type duration: :class:`datetime.timedelta`
    :param force: If the user is inactive, setting this to ``True`` will log
        them in regardless. Defaults to ``False``.
    :type force: bool
    :param fresh: setting this to ``False`` will log in the user with a session
        marked as not "fresh". Defaults to ``True``.
    :type fresh: bool
    """
    if not force and not user.is_active:
        return False

    user_id = getattr(user, current_app.login_manager.id_attribute)()
    session["_user_id"] = user_id
    session["_fresh"] = fresh
    session["_id"] = current_app.login_manager._session_identifier_generator()

    if remember:
        session["_remember"] = "set"
        if duration is not None:
            try:
                # equal to timedelta.total_seconds() but works with Python 2.6
                session["_remember_seconds"] = (
                    duration.microseconds
                    + (duration.seconds + duration.days * 24 * 3600) * 10**6
                ) / 10.0**6
            except AttributeError as e:
                raise Exception(
                    f"duration must be a datetime.timedelta, instead got: {duration}"
                ) from e

    current_app.login_manager._update_request_context_with_user(user)
    user_logged_in.send(current_app._get_current_object(), user=_get_user())
    return True

```

### `logout_user`
```python
def logout_user():
    """
    Logs a user out. (You do not need to pass the actual user.) This will
    also clean up the remember me cookie if it exists.
    """

    user = _get_user()

    if "_user_id" in session:
        session.pop("_user_id")

    if "_fresh" in session:
        session.pop("_fresh")

    if "_id" in session:
        session.pop("_id")

    cookie_name = current_app.config.get("REMEMBER_COOKIE_NAME", COOKIE_NAME)
    if cookie_name in request.cookies:
        session["_remember"] = "clear"
        if "_remember_seconds" in session:
            session.pop("_remember_seconds")

    user_logged_out.send(current_app._get_current_object(), user=user)

    current_app.login_manager._update_request_context_with_user()
    return True

```

### `unauthorized`
```python
    def unauthorized(self):
        """
        This is called when the user is required to log in. If you register a
        callback with :meth:`LoginManager.unauthorized_handler`, then it will
        be called. Otherwise, it will take the following actions:

            - Flash :attr:`LoginManager.login_message` to the user.

            - If the app is using blueprints find the login view for
              the current blueprint using `blueprint_login_views`. If the app
              is not using blueprints or the login view for the current
              blueprint is not specified use the value of `login_view`.

            - Redirect the user to the login view. (The page they were
              attempting to access will be passed in the ``next`` query
              string variable, so you can redirect there if present instead
              of the homepage. Alternatively, it will be added to the session
              as ``next`` if USE_SESSION_FOR_NEXT is set.)

        If :attr:`LoginManager.login_view` is not defined, then it will simply
        raise a HTTP 401 (Unauthorized) error instead.

        This should be returned from a view or before/after_request function,
        otherwise the redirect will have no effect.
        """
        user_unauthorized.send(current_app._get_current_object())

        if self.unauthorized_callback:
            return self.unauthorized_callback()

        if request.blueprint in self.blueprint_login_views:
            login_view = self.blueprint_login_views[request.blueprint]
        else:
            login_view = self.login_view

        if not login_view:
            abort(401)

        if self.login_message:
            if self.localize_callback is not None:
                flash(
                    self.localize_callback(self.login_message),
                    category=self.login_message_category,
                )
            else:
                flash(self.login_message, category=self.login_message_category)

        config = current_app.config
        if config.get("USE_SESSION_FOR_NEXT", USE_SESSION_FOR_NEXT):
            login_url = expand_login_view(login_view)
            session["_id"] = self._session_identifier_generator()
            session["next"] = make_next_param(login_url, request.url)
            redirect_url = make_login_url(login_view)
        else:
            redirect_url = make_login_url(login_view, next_url=request.url)

        return redirect(redirect_url)

```

## Flask-WTF CSRFProtect

### `CSRFProtect.protect`
```python
    def protect(self):
        if request.method not in current_app.config["WTF_CSRF_METHODS"]:
            return

        try:
            validate_csrf(self._get_csrf_token())
        except ValidationError as e:
            logger.info(e.args[0])
            self._error_response(e.args[0])

        if request.is_secure and current_app.config["WTF_CSRF_SSL_STRICT"]:
            if not request.referrer:
                self._error_response("The referrer header is missing.")

            good_referrer = f"https://{request.host}/"

            if not same_origin(request.referrer, good_referrer):
                self._error_response("The referrer does not match the host.")

        g.csrf_valid = True  # mark this request as CSRF valid

```

### `generate_csrf`
```python
def generate_csrf(secret_key=None, token_key=None):
    """Generate a CSRF token. The token is cached for a request, so multiple
    calls to this function will generate the same token.

    During testing, it might be useful to access the signed token in
    ``g.csrf_token`` and the raw token in ``session['csrf_token']``.

    :param secret_key: Used to securely sign the token. Default is
        ``WTF_CSRF_SECRET_KEY`` or ``SECRET_KEY``.
    :param token_key: Key where token is stored in session for comparison.
        Default is ``WTF_CSRF_FIELD_NAME`` or ``'csrf_token'``.
    """

    secret_key = _get_config(
        secret_key,
        "WTF_CSRF_SECRET_KEY",
        current_app.secret_key,
        message="A secret key is required to use CSRF.",
    )
    field_name = _get_config(
        token_key,
        "WTF_CSRF_FIELD_NAME",
        "csrf_token",
        message="A field name is required to use CSRF.",
    )

    if field_name not in g:
        s = URLSafeTimedSerializer(secret_key, salt="wtf-csrf-token")

        if field_name not in session:
            session[field_name] = hashlib.sha1(os.urandom(64)).hexdigest()

        try:
            token = s.dumps(session[field_name])
        except TypeError:
            session[field_name] = hashlib.sha1(os.urandom(64)).hexdigest()
            token = s.dumps(session[field_name])

        setattr(g, field_name, token)

    return g.get(field_name)

```

### `validate_csrf`
```python
def validate_csrf(data, secret_key=None, time_limit=None, token_key=None):
    """Check if the given data is a valid CSRF token. This compares the given
    signed token to the one stored in the session.

    :param data: The signed CSRF token to be checked.
    :param secret_key: Used to securely sign the token. Default is
        ``WTF_CSRF_SECRET_KEY`` or ``SECRET_KEY``.
    :param time_limit: Number of seconds that the token is valid. Default is
        ``WTF_CSRF_TIME_LIMIT`` or 3600 seconds (60 minutes).
    :param token_key: Key where token is stored in session for comparison.
        Default is ``WTF_CSRF_FIELD_NAME`` or ``'csrf_token'``.

    :raises ValidationError: Contains the reason that validation failed.

    .. versionchanged:: 0.14
        Raises ``ValidationError`` with a specific error message rather than
        returning ``True`` or ``False``.
    """

    secret_key = _get_config(
        secret_key,
        "WTF_CSRF_SECRET_KEY",
        current_app.secret_key,
        message="A secret key is required to use CSRF.",
    )
    field_name = _get_config(
        token_key,
        "WTF_CSRF_FIELD_NAME",
        "csrf_token",
        message="A field name is required to use CSRF.",
    )
    time_limit = _get_config(time_limit, "WTF_CSRF_TIME_LIMIT", 3600, required=False)

    if not data:
        raise ValidationError("The CSRF token is missing.")

    if field_name not in session:
        raise ValidationError("The CSRF session token is missing.")

    s = URLSafeTimedSerializer(secret_key, salt="wtf-csrf-token")

    try:
        token = s.loads(data, max_age=time_limit)
    except SignatureExpired as e:
        raise ValidationError("The CSRF token has expired.") from e
    except BadData as e:
        raise ValidationError("The CSRF token is invalid.") from e

    if not hmac.compare_digest(session[field_name], token):
        raise ValidationError("The CSRF tokens do not match.")

```

## Answers

- Does setting flask.g._login_user in a before_request override the session user? Yes, as seen in `_get_user` which checks `getattr(g, '_login_user', None)` first.

- Would token requests keep renewing the cookie user's session? Yes, because Flask-Session writes to the backend if the session is modified, or if `SESSION_REFRESH_EACH_REQUEST` is true (which it is by default).
- Flask hook order: `before_request` hooks run in the order they are registered. The `before_request` in `create_app` runs before blueprint hooks and route bodies.