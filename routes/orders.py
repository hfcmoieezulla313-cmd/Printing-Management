
from flask import Blueprint, render_template

from models import Order
from services.order_service import (
    tracking_timeline,
    advance_order_status_if_due,
)
from utils import login_required, current_user

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


# ---------------------------------------------------------
# Order Confirmation
# ---------------------------------------------------------

@orders_bp.route("/confirmation/<order_number>")
@login_required
def confirmation(order_number):

    user = current_user()

    order = Order.query.filter_by(
        order_number=order_number,
        user_id=user.id
    ).first_or_404()

    advance_order_status_if_due(order)

    return render_template(
        "customer/confirmation.html",
        order=order
    )


# ---------------------------------------------------------
# My Orders
# ---------------------------------------------------------

@orders_bp.route("/")
@login_required
def my_orders():

    user = current_user()

    orders = Order.query.filter_by(
        user_id=user.id
    ).order_by(
        Order.created_at.desc()
    ).all()

    for order in orders:
        advance_order_status_if_due(order)

    return render_template(
        "customer/orders.html",
        orders=orders
    )


# ---------------------------------------------------------
# Order Details
# ---------------------------------------------------------

@orders_bp.route("/<order_number>")
@login_required
def order_details(order_number):

    user = current_user()

    order = Order.query.filter_by(
        order_number=order_number,
        user_id=user.id
    ).first_or_404()

    advance_order_status_if_due(order)

    timeline = tracking_timeline(order)

    return render_template(
        "customer/order_details.html",
        order=order,
        timeline=timeline
    )


# ---------------------------------------------------------
# Track Order
# ---------------------------------------------------------

@orders_bp.route("/<order_number>/track")
@login_required
def track_order(order_number):

    user = current_user()

    order = Order.query.filter_by(
        order_number=order_number,
        user_id=user.id
    ).first_or_404()

    advance_order_status_if_due(order)

    timeline = tracking_timeline(order)

    return render_template(
        "customer/order_details.html",
        order=order,
        timeline=timeline,
        track_focus=True
    )
