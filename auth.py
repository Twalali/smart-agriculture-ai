from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def login_required_custom(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in.", "error")
            return redirect(url_for("auth_login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

def dashboard_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ("admin","government"):
            flash("Dashboard access required.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated

BURUNDI_PROVINCES = [
    "Bubanza","Bujumbura Mairie","Bujumbura Rural","Bururi",
    "Cankuzo","Cibitoke","Gitega","Karuzi","Kayanza",
    "Kirundo","Makamba","Muramvya","Muyinga","Mwaro",
    "Ngozi","Rumonge","Rutana","Ruyigi",
]
