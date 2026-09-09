"""Order creation / status / tracking logic. Kept separate from
routes/orders.py and routes/checkout.py so both can reuse it."""
import random
import string
from datetime import datetime

from models import db, Order, OrderItem, Notification
from models.order import ORDER_STATUSES
from services.pricing_service import compute_order_summary
from services.cart_service import clear_cart


def generate_order_number():
    """Professional order number: PM<year><5 random digits>, retried on
    the rare collision instead of trusting a raw DB integer ID."""
    year = datetime.utcnow().year
    for _ in range(10):
        suffix = "".join(random.choices(string.digits, k=5))
        candidate = f"PM{year}{suffix}"
        if not Order.query.filter_by(order_number=candidate).first():
            return candidate
    # Extremely unlikely fallback
    return f"PM{year}{int(datetime.utcnow().timestamp())}"


def create_order_from_cart(user, cart, address, coupon, payment_method):
    """Validates the cart, snapshots every item, creates the Order +
    OrderItems, decrements stationery stock, clears the cart, and
    returns the new Order. Raises ValueError on any business-rule
    violation (empty cart, below minimum order, out of stock, etc.)."""
    if not cart.items:
        raise ValueError("Your cart is empty.")

    summary = compute_order_summary(cart, coupon)
    totals = summary
    from services.pricing_service import compute_cart_totals
    cart_totals = compute_cart_totals(cart)
    if not cart_totals["meets_minimum_order"]:
        raise ValueError(
            f"Minimum order value is Rs. {cart_totals['minimum_order_value']:.2f}."
        )

    # Validate stationery stock before committing anything
    for item in cart.items:
        if item.item_type == "STATIONERY":
            product = item.stationery_product
            if not product or product.stock < item.quantity:
                raise ValueError(f"'{item.display_name()}' does not have enough stock.")

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

    for item in cart.items:
        if item.item_type == "PRINTING":
            cfg = item.print_configuration
            svc = cfg.printing_service if cfg else None
            details = (
                f"{svc.name if svc else 'Printing'} | {cfg.paper_size} | {cfg.print_type} | "
                f"{cfg.print_side} side | {cfg.copies} copies | Binding: {cfg.binding} | "
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
        else:
            product = item.stationery_product
            order_item = OrderItem(
                order_id=order.id,
                item_type="STATIONERY",
                name_snapshot=product.name if product else "Stationery item",
                details_snapshot=None,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                line_total=item.line_total(),
            )
            if product:
                product.stock = max(0, product.stock - item.quantity)
        db.session.add(order_item)

    notification = Notification(
        user_id=user.id,
        title="Order placed",
        message=f"Your order {order.order_number} has been placed successfully.",
    )
    db.session.add(notification)

    db.session.commit()
    clear_cart(user)
    return order


def update_order_status(order: Order, new_status: str):
    if new_status not in ORDER_STATUSES:
        raise ValueError("Invalid order status.")
    order.status = new_status
    db.session.add(Notification(
        user_id=order.user_id,
        title="Order status updated",
        message=f"Order {order.order_number} is now: {new_status}.",
    ))
    db.session.commit()
    return order


def tracking_timeline(order: Order):
    """Returns an ordered list of {label, done, current} for the UI."""
    if order.status == "Cancelled":
        return [{"label": "Order Placed", "done": True, "current": False},
                {"label": "Cancelled", "done": True, "current": True}]

    steps = ORDER_STATUSES[:-1]  # exclude "Cancelled" from the normal timeline
    current_index = steps.index(order.status) if order.status in steps else 0
    timeline = []
    for i, step in enumerate(steps):
        label = "Order Placed" if step == "Pending" else step
        timeline.append({
            "label": label,
            "done": i <= current_index,
            "current": i == current_index,
        })
    return timeline
