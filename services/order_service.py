
"""
Order creation, status management and tracking logic.

Used by routes/orders.py, routes/checkout.py and routes/admin.py.
"""

import random
import string
from datetime import datetime, timedelta

from models import db, Order, OrderItem, Notification
from models.order import ORDER_STATUSES

from services.pricing_service import (
    compute_order_summary,
    compute_cart_totals,
)
from services.cart_service import clear_cart


# ---------------------------------------------------------
# Generate Order Number
# ---------------------------------------------------------

def generate_order_number():
    """Generate a professional order number: PM<year><5 digits>."""

    year = datetime.utcnow().year

    for _ in range(10):
        suffix = "".join(random.choices(string.digits, k=5))
        candidate = f"PM{year}{suffix}"

        if not Order.query.filter_by(order_number=candidate).first():
            return candidate

    return f"PM{year}{int(datetime.utcnow().timestamp())}"


# ---------------------------------------------------------
# Create Order
# ---------------------------------------------------------

def create_order_from_cart(
    user,
    cart,
    address,
    coupon,
    payment_method,
):
    """
    Validate cart, create order and order items,
    create notification and clear cart after success.
    """

    if not cart.items:
        raise ValueError("Your cart is empty.")

    summary = compute_order_summary(cart, coupon)
    cart_totals = compute_cart_totals(cart)

    if not cart_totals["meets_minimum_order"]:
        raise ValueError(
            f"Minimum order value is "
            f"Rs. {cart_totals['minimum_order_value']:.2f}."
        )

    # Create order
    order = Order(
        order_number=generate_order_number(),
        user_id=user.id,
        address_id=address.id,
        coupon_id=coupon.id if coupon else None,

        subtotal=summary["subtotal"],
        delivery_charge=summary["delivery_charge"],
        discount_amount=summary["discount_amount"],
        total_amount=summary["total_amount"],

        payment_method=payment_method,
        status="Confirmed",

        contact_name=address.contact_name,
        contact_phone=address.contact_phone,
    )

    db.session.add(order)
    db.session.flush()

    # Create order items
    for item in cart.items:

        # PRINTING
        if item.item_type == "PRINTING":

            cfg = item.print_configuration
            svc = cfg.printing_service if cfg else None

            if not cfg:
                raise ValueError(
                    "Printing configuration is missing."
                )

            details = (
                f"{svc.name if svc else 'Printing'} | "
                f"{cfg.paper_size} | "
                f"{cfg.print_type} | "
                f"{cfg.print_side} side | "
                f"{cfg.copies} copies | "
                f"Binding: {cfg.binding} | "
                f"{cfg.page_count} pages/copy"
            )

            order_item = OrderItem(
                order_id=order.id,
                item_type="PRINTING",
                name_snapshot=svc.name if svc else "Printing item",
                details_snapshot=details,
                quantity=1,
                unit_price=item.line_total(),
                line_total=item.line_total(),
            )

        # NORMAL PHOTO
        elif item.item_type == "PHOTO":

            cfg = item.photo_configuration

            if not cfg:
                raise ValueError(
                    "Photo configuration is missing."
                )

            details = (
                f"Size: {cfg.photo_size} | "
                f"Frame: {cfg.frame or 'NONE'} | "
                f"Copies: {cfg.quantity}"
            )

            order_item = OrderItem(
                order_id=order.id,
                item_type="PHOTO",
                name_snapshot="Photo Printing",
                details_snapshot=details,
                quantity=1,
                unit_price=item.line_total(),
                line_total=item.line_total(),
            )

        # PASSPORT PHOTO
        elif item.item_type == "PASSPORT":

            cfg = item.photo_configuration

            if not cfg:
                raise ValueError(
                    "Passport photo configuration is missing."
                )

            details = f"Quantity: {cfg.quantity}"

            order_item = OrderItem(
                order_id=order.id,
                item_type="PASSPORT",
                name_snapshot="Passport Photo",
                details_snapshot=details,
                quantity=1,
                unit_price=item.line_total(),
                line_total=item.line_total(),
            )

        else:
            raise ValueError(
                f"Unsupported cart item type: {item.item_type}"
            )

        db.session.add(order_item)

    # Create notification
    notification = Notification(
        user_id=user.id,
        title="Order confirmed",
        message=(
            f"Your order {order.order_number} "
            f"has been confirmed successfully."
        ),
    )

    db.session.add(notification)

    # Save order and items
    db.session.commit()

    # Clear cart after successful order
    clear_cart(user)

    return order


# ---------------------------------------------------------
# Update Order Status
# ---------------------------------------------------------

def update_order_status(order: Order, new_status: str):
    """Update an order status and notify the customer."""

    if new_status not in ORDER_STATUSES:
        raise ValueError("Invalid order status.")

    if order.status == "Cancelled":
        raise ValueError("A cancelled order cannot be updated.")

    if order.status == "Delivered":
        raise ValueError("A delivered order cannot be updated.")

    order.status = new_status

    notification = Notification(
        user_id=order.user_id,
        title="Order status updated",
        message=(
            f"Order {order.order_number} "
            f"is now: {new_status}."
        ),
    )

    db.session.add(notification)
    db.session.commit()

    return order


# ---------------------------------------------------------
# Automatic Order Status Updates
# ---------------------------------------------------------

def advance_order_status_if_due(order: Order):
    """
    Automatically advance order status based on order creation time.

    Immediately: Confirmed
    After 5 minutes: Printing
    After 10 minutes: Ready for Delivery

    Out for Delivery and Delivered remain admin-controlled.
    """

    if order.status in (
        "Cancelled",
        "Out for Delivery",
        "Delivered",
        "Ready for Delivery",
    ):
        return order

    if not order.created_at:
        return order

    elapsed = datetime.utcnow() - order.created_at

    if elapsed >= timedelta(minutes=10):
        target_status = "Ready for Delivery"

    elif elapsed >= timedelta(minutes=5):
        target_status = "Printing"

    else:
        target_status = "Confirmed"

    if order.status != target_status:
        update_order_status(order, target_status)

    return order


# ---------------------------------------------------------
# Customer Tracking Timeline
# ---------------------------------------------------------

def tracking_timeline(order: Order):
    """Return tracking steps for the customer order page."""

    if order.status == "Cancelled":
        return [
            {
                "label": "Order Placed",
                "done": True,
                "current": False,
            },
            {
                "label": "Cancelled",
                "done": True,
                "current": True,
            },
        ]

    steps = ORDER_STATUSES[:-1]

    current_index = (
        steps.index(order.status)
        if order.status in steps
        else 0
    )

    timeline = []

    for i, step in enumerate(steps):

        label = (
            "Order Placed"
            if step == "Pending"
            else step
        )

        timeline.append({
            "label": label,
            "done": i <= current_index,
            "current": i == current_index,
        })

    return timeline
