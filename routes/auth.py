import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db, User
from utils import current_user

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("main.home"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not EMAIL_RE.match(email):
            errors.append("Enter a valid email address.")
        if not re.match(r"^\d{10}$", phone):
            errors.append("Enter a valid 10-digit phone number.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        if User.query.filter_by(phone=phone).first():
            errors.append("An account with this phone number already exists.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html", form=request.form)

        user = User(full_name=full_name, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session.clear()
        session["user_id"] = user.id
        flash("Welcome to PrintCare! Your account has been created.", "success")
        return redirect(url_for("main.home"))

    return render_template("auth/register.html", form={})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("main.home"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.email == identifier) | (User.phone == identifier)
        ).first()

        if not user or not user.check_password(password):
            flash("Invalid credentials. Please try again.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("This account has been disabled. Contact support.", "danger")
            return render_template("auth/login.html")

        session.clear()
        session["user_id"] = user.id
        flash(f"Welcome back, {user.full_name.split(' ')[0]}!", "success")
        next_url = request.args.get("next") or url_for("main.home")
        return redirect(next_url)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
