import re
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from werkzeug.security import generate_password_hash

from models import db, User
from utils import current_user


auth_bp = Blueprint("auth", __name__)


# -----------------------------
# Validation
# -----------------------------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# OTP is valid for 5 minutes
OTP_EXPIRY_MINUTES = 5


# -----------------------------
# Send OTP Email
# -----------------------------

def send_otp_email(email, otp):
    """
    Sends the OTP to the user's email.

    SMTP settings are taken from environment variables.
    """

    import os

    smtp_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("MAIL_PORT", "587"))
    smtp_username = os.environ.get("MAIL_USERNAME", "")
    smtp_password = os.environ.get("MAIL_PASSWORD", "")
    mail_from = os.environ.get("MAIL_FROM", smtp_username)

    if not smtp_username or not smtp_password:
        print("MAIL_USERNAME or MAIL_PASSWORD is not configured.")
        return False

    message = EmailMessage()

    message["Subject"] = "Your PrintPilot AI Verification Code"
    message["From"] = mail_from
    message["To"] = email

    message.set_content(
        f"""
Hello,

Welcome to PrintPilot AI!

Your account verification OTP is:

{otp}

This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.

If you did not request this code, you can safely ignore this email.

Regards,
PrintPilot AI
Printing made smarter
"""
    )

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)

        return True

    except Exception as e:
        print("OTP email error:", e)
        return False


# -----------------------------
# Register
# -----------------------------

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

        # -----------------------------
        # Validation
        # -----------------------------

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

        # -----------------------------
        # Check existing account
        # -----------------------------

        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")

        if User.query.filter_by(phone=phone).first():
            errors.append("An account with this phone number already exists.")

        if errors:

            for error in errors:
                flash(error, "danger")

            return render_template(
                "auth/register.html",
                form=request.form
            )

        # -----------------------------
        # Generate OTP
        # -----------------------------

        otp = str(secrets.randbelow(900000) + 100000)

        # Store registration temporarily in session
        # Password is HASHED before being stored.
        session["pending_registration"] = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password_hash": generate_password_hash(password),
            "otp_hash": generate_password_hash(otp),
            "otp_expires": (
                datetime.utcnow() +
                timedelta(minutes=OTP_EXPIRY_MINUTES)
            ).isoformat(),
        }

        # -----------------------------
        # Send OTP
        # -----------------------------

        if not send_otp_email(email, otp):

            session.pop("pending_registration", None)

            flash(
                "We could not send the verification code. "
                "Please check the email configuration.",
                "danger"
            )

            return render_template(
                "auth/register.html",
                form=request.form
            )

        flash(
            "Verification code sent to your email.",
            "success"
        )

        return redirect(url_for("auth.verify_otp"))

    return render_template(
        "auth/register.html",
        form={}
    )


# -----------------------------
# Verify OTP
# -----------------------------

@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    if current_user():
        return redirect(url_for("main.home"))

    pending = session.get("pending_registration")

    if not pending:
        flash(
            "Your registration session has expired. Please register again.",
            "danger"
        )

        return redirect(url_for("auth.register"))

    if request.method == "POST":

        entered_otp = request.form.get("otp", "").strip()

        if not re.match(r"^\d{6}$", entered_otp):

            flash(
                "Enter the 6-digit verification code.",
                "danger"
            )

            return render_template(
                "auth/verify_otp.html",
                email=pending["email"]
            )

        # -----------------------------
        # Check expiry
        # -----------------------------

        try:
            expiry_time = datetime.fromisoformat(
                pending["otp_expires"]
            )

        except ValueError:

            session.pop("pending_registration", None)

            flash(
                "Invalid verification session. Please register again.",
                "danger"
            )

            return redirect(url_for("auth.register"))

        if datetime.utcnow() > expiry_time:

            session.pop("pending_registration", None)

            flash(
                "The OTP has expired. Please register again.",
                "danger"
            )

            return redirect(url_for("auth.register"))

        # -----------------------------
        # Check OTP
        # -----------------------------

        from werkzeug.security import check_password_hash

        if not check_password_hash(
            pending["otp_hash"],
            entered_otp
        ):

            flash(
                "Incorrect verification code.",
                "danger"
            )

            return render_template(
                "auth/verify_otp.html",
                email=pending["email"]
            )

        # -----------------------------
        # Check account again
        # -----------------------------

        if User.query.filter_by(
            email=pending["email"]
        ).first():

            session.pop("pending_registration", None)

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return redirect(url_for("auth.login"))

        if User.query.filter_by(
            phone=pending["phone"]
        ).first():

            session.pop("pending_registration", None)

            flash(
                "An account with this phone number already exists.",
                "danger"
            )

            return redirect(url_for("auth.login"))

        # -----------------------------
        # Create User
        # -----------------------------

        user = User(
            full_name=pending["full_name"],
            email=pending["email"],
            phone=pending["phone"],
            password_hash=pending["password_hash"],
        )

        db.session.add(user)
        db.session.commit()

        # Clear temporary registration data
        session.pop("pending_registration", None)

        flash(
            "Your account has been created successfully. "
            "You can now log in.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template(
        "auth/verify_otp.html",
        email=pending["email"]
    )


# -----------------------------
# Resend OTP
# -----------------------------

@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():

    if current_user():
        return redirect(url_for("main.home"))

    pending = session.get("pending_registration")

    if not pending:
        flash(
            "Your registration session has expired. Please register again.",
            "danger"
        )

        return redirect(url_for("auth.register"))

    # Generate new OTP
    otp = str(secrets.randbelow(900000) + 100000)

    pending["otp_hash"] = generate_password_hash(otp)

    pending["otp_expires"] = (
        datetime.utcnow() +
        timedelta(minutes=OTP_EXPIRY_MINUTES)
    ).isoformat()

    session["pending_registration"] = pending

    if not send_otp_email(
        pending["email"],
        otp
    ):

        flash(
            "Could not resend the OTP. Please try again.",
            "danger"
        )

        return redirect(url_for("auth.verify_otp"))

    flash(
        "A new verification code has been sent.",
        "success"
    )

    return redirect(url_for("auth.verify_otp"))


# -----------------------------
# Login
# -----------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user():
        return redirect(url_for("main.home"))

    if request.method == "POST":

        identifier = request.form.get(
            "identifier",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter(
            (User.email == identifier) |
            (User.phone == identifier)
        ).first()

        if not user or not user.check_password(password):

            flash(
                "Invalid credentials. Please try again.",
                "danger"
            )

            return render_template(
                "auth/login.html"
            )

        if not user.is_active:

            flash(
                "This account has been disabled. Contact support.",
                "danger"
            )

            return render_template(
                "auth/login.html"
            )

        session.clear()

        session["user_id"] = user.id

        flash(
            f"Welcome back, {user.full_name.split(' ')[0]}!",
            "success"
        )

        next_url = (
            request.args.get("next")
            or url_for("main.home")
        )

        return redirect(next_url)

    return render_template(
        "auth/login.html"
    )


# -----------------------------
# Logout
# -----------------------------

@auth_bp.route("/logout")
def logout():

    session.pop("user_id", None)

    flash(
        "You have been logged out.",
        "info"
    )

    return redirect(
        url_for("auth.login")
    )