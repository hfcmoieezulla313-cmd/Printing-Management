from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify

from models import db, Address, Coupon
from services.cart_service import get_or_create_cart
from services.pricing_service import compute_order_summary, compute_cart_totals
from services.order_service import create_order_from_cart
from utils import login_required, current_user

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")


@checkout_bp.route("/", methods=["GET"])
@login_required
def checkout():
    user = current_user()
    cart = get_or_create_cart(user)
    if not cart.items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart.view_cart"))

    addresses = Address.query.filter_by(user_id=user.id).order_by(Address.is_default.desc()).all()
    coupon_code = session.get("coupon_code")
    coupon = Coupon.query.filter_by(code=coupon_code).first() if coupon_code else None
    summary = compute_order_summary(cart, coupon)

    return render_template("customer/checkout.html", cart=cart, addresses=addresses,
                            summary=summary, applied_coupon=coupon)


@checkout_bp.route("/apply-coupon", methods=["POST"])
@login_required
def apply_coupon():
    code = request.form.get("code", "").strip().upper()
    user = current_user()
    cart = get_or_create_cart(user)
    totals = compute_cart_totals(cart)

    coupon = Coupon.query.filter_by(code=code).first()
    from services.pricing_service import apply_coupon as validate_coupon
    valid, discount, message = validate_coupon(coupon, totals["subtotal"])

    if valid:
        session["coupon_code"] = code
        flash(message, "success")
    else:
        session.pop("coupon_code", None)
        flash(message, "danger")

    return redirect(url_for("checkout.checkout"))


@checkout_bp.route("/remove-coupon", methods=["POST"])
@login_required
def remove_coupon():
    session.pop("coupon_code", None)
    flash("Coupon removed.", "info")
    return redirect(url_for("checkout.checkout"))


@checkout_bp.route("/place-order", methods=["POST"])
@login_required
def place_order():
    user = current_user()
    cart = get_or_create_cart(user)
    address_id = request.form.get("address_id", type=int)
    payment_method = request.form.get("payment_method", "COD")

    address = Address.query.filter_by(id=address_id, user_id=user.id).first()
    if not address:
        flash("Please select a valid delivery address.", "danger")
        return redirect(url_for("checkout.checkout"))

    coupon_code = session.get("coupon_code")
    coupon = Coupon.query.filter_by(code=coupon_code).first() if coupon_code else None

    try:
        order = create_order_from_cart(user, cart, address, coupon, payment_method)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("checkout.checkout"))

    session.pop("coupon_code", None)
    return redirect(url_for("orders.confirmation", order_number=order.order_number))
