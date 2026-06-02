"""
auth.py — Authentication helpers and route decorators.
"""

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def farmer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("auth_login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in.", "error")
            return redirect(url_for("auth_login"))
        if not current_user.is_admin:
            flash("Access denied. Admin only.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


def dashboard_required(f):
    """Admin or Government access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in.", "error")
            return redirect(url_for("auth_login"))
        if current_user.role not in ("admin", "government"):
            flash("Access denied.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


BURUNDI_PROVINCES = [
    "Bubanza", "Bujumbura Mairie", "Bujumbura Rural", "Bururi",
    "Cankuzo", "Cibitoke", "Gitega", "Karuzi", "Kayanza",
    "Kirundo", "Makamba", "Muramvya", "Muyinga", "Mwaro",
    "Ngozi", "Rumonge", "Rutana", "Ruyigi",
]
