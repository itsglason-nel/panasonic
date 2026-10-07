Base commit: 0d7b700

# A5 AUTH AND SESSION INTERNALS

- **Login routes**: `auth.login` handles POST, checks `is_locked_out`, calls `login_user(user)`.
- **user_loader**: `LoginManager.user_loader` queries `User.query.get(id)`.
- **unauthorized**: Redirects to `auth.login` and flashes a message.
- **session keys**: `_user_id`, `_flashes`, `selected_module`.
