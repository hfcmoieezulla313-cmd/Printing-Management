from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import db, Complaint, Order, Setting
from utils import login_required, current_user

support_bp = Blueprint("support", __name__)


@support_bp.route("/support", methods=["GET", "POST"])
@login_required
def support():
    user = current_user()

    if request.method == "POST":
        category = request.form.get("category", "Other")
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        order_number = request.form.get("order_number", "").strip()

        if not subject or not message:
            flash("Please fill in the subject and message.", "danger")
        else:
            order = None
            if order_number:
                order = Order.query.filter_by(order_number=order_number, user_id=user.id).first()
            complaint = Complaint(
                user_id=user.id,
                order_id=order.id if order else None,
                category=category,
                subject=subject,
                message=message,
            )
            db.session.add(complaint)
            db.session.commit()
            flash("Your request has been submitted. Our team will get back to you soon.", "success")
            return redirect(url_for("support.support"))

    my_complaints = Complaint.query.filter_by(user_id=user.id).order_by(Complaint.created_at.desc()).all()
    support_phone = Setting.get("support_phone", "1800-000-0000")
    support_email = Setting.get("support_email", "support@printcare.local")
    return render_template("customer/complaints.html", complaints=my_complaints,
                            support_phone=support_phone, support_email=support_email)
