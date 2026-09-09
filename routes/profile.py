from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import db, Address, Notification
from utils import login_required, current_user

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def profile():
    return render_template("customer/profile.html", user=current_user())


@profile_bp.route("/profile/edit", methods=["POST"])
@login_required
def edit_profile():
    user = current_user()
    user.full_name = request.form.get("full_name", user.full_name).strip()
    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("profile.profile"))


@profile_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    user = current_user()
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not user.check_password(current_password):
        flash("Current password is incorrect.", "danger")
    elif len(new_password) < 6:
        flash("New password must be at least 6 characters.", "danger")
    elif new_password != confirm_password:
        flash("New passwords do not match.", "danger")
    else:
        user.set_password(new_password)
        db.session.commit()
        flash("Password changed successfully.", "success")
    return redirect(url_for("profile.profile"))


@profile_bp.route("/addresses")
@login_required
def addresses():
    user = current_user()
    address_list = Address.query.filter_by(user_id=user.id).order_by(Address.is_default.desc()).all()
    return render_template("customer/addresses.html", addresses=address_list)


@profile_bp.route("/addresses/add", methods=["POST"])
@login_required
def add_address():
    user = current_user()
    if request.form.get("is_default") == "on":
        Address.query.filter_by(user_id=user.id).update({"is_default": False})

    address = Address(
        user_id=user.id,
        label=request.form.get("label", "Home"),
        contact_name=request.form.get("contact_name", "").strip(),
        contact_phone=request.form.get("contact_phone", "").strip(),
        line1=request.form.get("line1", "").strip(),
        line2=request.form.get("line2", "").strip(),
        city=request.form.get("city", "").strip(),
        state=request.form.get("state", "").strip(),
        pincode=request.form.get("pincode", "").strip(),
        is_default=request.form.get("is_default") == "on",
    )
    db.session.add(address)
    db.session.commit()
    flash("Address added.", "success")
    return redirect(request.referrer or url_for("profile.addresses"))


@profile_bp.route("/addresses/<int:address_id>/delete", methods=["POST"])
@login_required
def delete_address(address_id):
    user = current_user()
    address = Address.query.filter_by(id=address_id, user_id=user.id).first_or_404()
    db.session.delete(address)
    db.session.commit()
    flash("Address removed.", "info")
    return redirect(url_for("profile.addresses"))


@profile_bp.route("/notifications")
@login_required
def notifications():
    user = current_user()
    items = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return render_template("customer/notifications.html", notifications=items)
