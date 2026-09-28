"""
Order creation / status / tracking logic.

Kept separate from routes/orders.py and routes/checkout.py
so both can reuse the same business logic.
"""

import random
import string
from datetime import datetime

from models import db, Order, OrderItem, Notification

from models.order import ORDER_STATUSES

from services.pricing_service import compute_order_summary

from services.cart_service import clear_cart


def generate_order_number():
    """
    Professional order number:
    PM<year><5 random digits>

    Retries on the rare collision instead of trusting a raw DB integer ID.
    """

    year = datetime.utcnow().year

    for _ in range(10):
        suffix = "".join(
            random.choices(string.digits, k=5)
        )

        candidate = f"PM{year}{suffix}"

        if not Order.query.filter_by(
            order_number=candidate
        ).first():
            return candidate

    # Extremely unlikely fallback
    return f"PM{year}{int(datetime.utcnow().timestamp())}"


def create_order_from_cart(
    user,
    cart,
    address,
    coupon,
    payment_method,
):
    """
    Validates the cart, snapshots every item, creates the Order
    and OrderItems, decrements stationery stock, clears the cart,
    and returns the new Order.

    Raises ValueError when a business rule is violated.
    """

    if not cart.items:
        raise ValueError("Your cart is empty.")

    # Calculate final order totals
    summary = compute_order_summary(
        cart,
        coupon
    )

    totals = summary

    from services.pricing_service import compute_cart_totals

    cart_totals = compute_cart_totals(cart)

    if not cart_totals["meets_minimum_order"]:
        raise ValueError(
            f"Minimum order value is "
            f"Rs. {cart_totals['minimum_order_value']:.2f}."
        )

    # ---------------------------------------------------------
    # Validate stationery stock before committing anything
    # ---------------------------------------------------------

    for item in cart.items:

        if item.item_type == "STATIONERY":

            product = item.stationery_product

            if not product or product.stock < item.quantity:

                raise ValueError(
                    f"'{item.display_name()}' does not have enough stock."
                )

    # ---------------------------------------------------------
    # Create order
    # ---------------------------------------------------------

    order = Order(
        order_number=generate_order_number(),
        user_id=user.id,
        address_id=address.id,
        coupon_id=coupon.id if coupon else None,

        subtotal=totals["subtotal"],
        delivery_charge=totals["delivery_charge"],
        discount_amount=totals["discount_amount"],
        total_amount=totals["total_amount"],

        payment_method=payment_method,
        status="Pending",

        contact_name=address.contact_name,
        contact_phone=address.contact_phone,
    )

    db.session.add(order)

    db.session.flush()

    # ---------------------------------------------------------
    # Convert every cart item into an order item
    # ---------------------------------------------------------

    for item in cart.items:

        # =====================================================
        # PRINTING
        # =====================================================

        if item.item_type == "PRINTING":

            cfg = item.print_configuration

            svc = cfg.printing_service if cfg else None

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

                name_snapshot=(
                    svc.name
                    if svc
                    else "Printing item"
                ),

                details_snapshot=details,

                quantity=1,

                unit_price=item.line_total(),

                line_total=item.line_total(),
            )

        # =====================================================
        # NORMAL PHOTO
        # =====================================================

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

        # =====================================================
        # PASSPORT PHOTO
        # =====================================================

        elif item.item_type == "PASSPORT":

            cfg = item.photo_configuration

            if not cfg:

                raise ValueError(
                    "Passport photo configuration is missing."
                )

            details = (
                f"Quantity: {cfg.quantity}"
            )

            order_item = OrderItem(
                order_id=order.id,

                item_type="PASSPORT",

                name_snapshot="Passport Photo",

                details_snapshot=details,

                quantity=1,

                unit_price=item.line_total(),

                line_total=item.line_total(),
            )

        # =====================================================
        # STATIONERY
        # =====================================================

        elif item.item_type == "STATIONERY":

            product = item.stationery_product

            order_item = OrderItem(
                order_id=order.id,

                item_type="STATIONERY",

                name_snapshot=(
                    product.name
                    if product
                    else "Stationery item"
                ),

                details_snapshot=None,

                quantity=item.quantity,

                unit_price=float(
                    item.unit_price
                ),

                line_total=item.line_total(),
            )

            # Reduce stationery stock
            if product:

                product.stock = max(
                    0,
                    product.stock - item.quantity
                )

        # =====================================================
        # UNKNOWN ITEM TYPE
        # =====================================================

        else:

            raise ValueError(
                f"Unsupported cart item type: "
                f"{item.item_type}"
            )

        db.session.add(order_item)

    # ---------------------------------------------------------
    # Notification
    # ---------------------------------------------------------

    notification = Notification(
        user_id=user.id,

        title="Order placed",

        message=(
            f"Your order {order.order_number} "
            f"has been placed successfully."
        ),
    )

    db.session.add(notification)

    # ---------------------------------------------------------
    # Save everything
    # ---------------------------------------------------------

    db.session.commit()

    # Clear cart after successful order
    clear_cart(user)

    return order


def update_order_status(
    order: Order,
    new_status: str,
):
    """Update an order status and create a notification."""

    if new_status not in ORDER_STATUSES:

        raise ValueError(
            "Invalid order status."
        )

    order.status = new_status

    db.session.add(
        Notification(
            user_id=order.user_id,

            title="Order status updated",

            message=(
                f"Order {order.order_number} "
                f"is now: {new_status}."
            ),
        )
    )

    db.session.commit()

    return order


def tracking_timeline(order: Order):
    """
    Returns an ordered list of:
    {label, done, current}
    for the tracking UI.
    """

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

        timeline.append(
            {
                "label": label,
                "done": i <= current_index,
                "current": i == current_index,
            }
        )

    return timeline