from functools import wraps
from flask import abort
from flask_login import current_user


def applicant_required(f):
    """Restrict a route to logged-in users who have an applicant profile."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.applicant is None:
            abort(403)
        return f(*args, **kwargs)
    return wrapped


def admin_required(f):
    """Restrict a route to logged-in users with role='admin'."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return wrapped


def permission_required(scope):
    """
    Restrict a route to admins who either are a super admin or have been
    explicitly granted this permission scope. Use *under* @admin_required:

        @admin_bp.route(...)
        @login_required
        @admin_required
        @permission_required("documents")
        def verify_document(): ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_permission(scope):
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def super_admin_required(f):
    """Restrict a route to super admins only — used for team/permission management."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin() or not current_user.is_super_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapped
