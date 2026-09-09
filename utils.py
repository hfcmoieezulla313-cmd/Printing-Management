"""Small shared helpers: auth decorators + current-user lookups.
Kept at the project root (not inside routes/) so both customer and
admin blueprints can import it without circular imports."""
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify

from models import User, Admin


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def current_admin():
    admin_id = session.get("admin_id")
    if not admin_id:
        return None
    return Admin.query.get(admin_id)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Please log in."}), 401
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in as admin.", "warning")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapped
