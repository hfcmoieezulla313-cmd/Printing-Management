"""
All price math lives here. Routes call into this module instead of
computing totals themselves - this is the ONE place to look (or edit)
if pricing rules change, and it means the client can never be trusted
to supply a price (we always recompute server-side).
"""
from decimal import Decimal, ROUND_HALF_UP
from models import db, Setting


def _money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_print_price(printing_service, paper_size, print_type, print_side, copies, binding, page_count):
    """Server-side calculation for one printing configuration.
    Returns a dict with a full breakdown plus 'total'."""
    copies = max(1, int(copies or 1))
    page_count = max(1, int(page_count or 1))

    if printing_service.is_configurable:
        price_per_page = Decimal(str(printing_service.price_per_page or 0))
        if print_side == "DOUBLE":
            price_per_page += Decimal(str(printing_service.double_side_extra or 0))
        printing_subtotal = price_per_page * page_count * copies
    else:
        printing_subtotal = Decimal(str(printing_service.flat_price or 0)) * copies
        price_per_page = Decimal(str(printing_service.flat_price or 0))

    binding_cost = Decimal("0")
    if binding == "SPIRAL":
        spiral_price = Decimal(str(Setting.get_float("spiral_binding_price", 20)))
        binding_cost = spiral_price * copies

    total = printing_subtotal + binding_cost

    return {
        "price_per_page": float(_money(price_per_page)),
        "printing_subtotal": float(_money(printing_subtotal)),
        "binding_cost": float(_money(binding_cost)),
        "total": float(_money(total)),
    }


def compute_cart_totals(cart):
    subtotal = Decimal("0")
    for item in cart.items:
        subtotal += Decimal(str(item.line_total()))

    min_order = Decimal(str(Setting.get_float("minimum_order_value", 100)))
    free_delivery_threshold = Decimal(str(Setting.get_float("free_delivery_threshold", 100)))
    delivery_charge_setting = Decimal(str(Setting.get_float("delivery_charge", 30)))

    if subtotal >= free_delivery_threshold:
        delivery_charge = Decimal("0")
    else:
        delivery_charge = delivery_charge_setting

    return {
        "subtotal": float(_money(subtotal)),
        "delivery_charge": float(_money(delivery_charge)),
        "minimum_order_value": float(_money(min_order)),
        "meets_minimum_order": subtotal >= min_order,
        "free_delivery_threshold": float(_money(free_delivery_threshold)),
    }


def apply_coupon(coupon, subtotal):
    """Validate + compute discount for a coupon against a given subtotal.
    Returns (is_valid, discount_amount, message)."""
    subtotal = Decimal(str(subtotal))

    if coupon is None:
        return False, Decimal("0"), "Invalid coupon code."
    if not coupon.is_valid_now():
        return False, Decimal("0"), "This coupon is inactive or has expired."
    if subtotal < Decimal(str(coupon.minimum_order_value or 0)):
        return False, Decimal("0"), (
            f"Minimum order of Rs. {coupon.minimum_order_value} required for this coupon."
        )

    if coupon.discount_type == "PERCENT":
        discount = subtotal * Decimal(str(coupon.discount_value)) / Decimal("100")
        if coupon.maximum_discount is not None:
            discount = min(discount, Decimal(str(coupon.maximum_discount)))
    else:  # FIXED
        discount = Decimal(str(coupon.discount_value))

    discount = min(discount, subtotal)  # never discount more than the order is worth
    return True, _money(discount), "Coupon applied successfully."


def compute_order_summary(cart, coupon=None):
    """Full checkout-time summary: subtotal, delivery, discount, total."""
    totals = compute_cart_totals(cart)
    subtotal = Decimal(str(totals["subtotal"]))
    delivery_charge = Decimal(str(totals["delivery_charge"]))

    discount = Decimal("0")
    coupon_message = None
    if coupon is not None:
        valid, discount, coupon_message = apply_coupon(coupon, subtotal)
        if not valid:
            discount = Decimal("0")

    total = subtotal + delivery_charge - discount
    if total < 0:
        total = Decimal("0")

    return {
        "subtotal": float(_money(subtotal)),
        "delivery_charge": float(_money(delivery_charge)),
        "discount_amount": float(_money(discount)),
        "total_amount": float(_money(total)),
        "coupon_message": coupon_message,
    }
