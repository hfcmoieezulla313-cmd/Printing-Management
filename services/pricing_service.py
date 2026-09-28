"""
All price math lives here.

Routes call into this module instead of computing totals themselves.
The client can never be trusted to supply a price because all totals
are calculated again on the server.
"""

from decimal import Decimal, ROUND_HALF_UP

from models import Setting


def _money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# ============================================================
# PRINTING
# ============================================================

def compute_print_price(
    printing_service,
    paper_size,
    print_type,
    print_side,
    copies,
    binding,
    page_count,
):
    """Server-side calculation for one printing configuration."""

    copies = max(1, int(copies or 1))
    page_count = max(1, int(page_count or 1))

    if printing_service.is_configurable:
        price_per_page = Decimal(
            str(printing_service.price_per_page or 0)
        )

        if print_side == "DOUBLE":
            price_per_page += Decimal(
                str(printing_service.double_side_extra or 0)
            )

        printing_subtotal = (
            price_per_page
            * page_count
            * copies
        )

    else:
        printing_subtotal = (
            Decimal(
                str(printing_service.flat_price or 0)
            ) * copies
        )

        price_per_page = Decimal(
            str(printing_service.flat_price or 0)
        )

    binding_cost = Decimal("0")

    if binding == "SPIRAL":
        spiral_price = Decimal(
            str(
                Setting.get_float(
                    "spiral_binding_price",
                    20
                )
            )
        )

        binding_cost = spiral_price * copies

    total = printing_subtotal + binding_cost

    return {
        "price_per_page": float(
            _money(price_per_page)
        ),
        "printing_subtotal": float(
            _money(printing_subtotal)
        ),
        "binding_cost": float(
            _money(binding_cost)
        ),
        "total": float(
            _money(total)
        ),
    }


# ============================================================
# NORMAL PHOTO
# ============================================================

PHOTO_PRICES = {
    "4x6": Decimal("20.00"),
    "5x7": Decimal("30.00"),
    "6x8": Decimal("40.00"),
}

FRAME_PRICES = {
    "NONE": Decimal("0.00"),
    "WHITE": Decimal("80.00"),
    "BLACK": Decimal("90.00"),
    "PREMIUM": Decimal("120.00"),
}


def compute_photo_price(
    photo_size,
    frame,
    quantity,
):
    """
    Server-side price calculation for normal photo printing.

    Photo prices:
        4x6      = Rs. 20
        5x7      = Rs. 30
        6x8      = Rs. 40

    Frame prices:
        NONE     = Rs. 0
        WHITE    = Rs. 80
        BLACK    = Rs. 90
        PREMIUM  = Rs. 120

    Frame price is charged per copy.
    """

    if photo_size not in PHOTO_PRICES:
        raise ValueError("Invalid photo size.")

    frame = (frame or "NONE").upper()

    if frame not in FRAME_PRICES:
        raise ValueError("Invalid photo frame.")

    quantity = max(
        1,
        min(100, int(quantity or 1))
    )

    price_per_copy = PHOTO_PRICES[photo_size]
    frame_price_per_copy = FRAME_PRICES[frame]

    photo_subtotal = (
        price_per_copy * quantity
    )

    frame_subtotal = (
        frame_price_per_copy * quantity
    )

    total = (
        photo_subtotal
        + frame_subtotal
    )

    return {
        "photo_size": photo_size,
        "frame": frame,
        "quantity": quantity,

        "price_per_copy": float(
            _money(price_per_copy)
        ),

        "frame_price_per_copy": float(
            _money(frame_price_per_copy)
        ),

        "photo_subtotal": float(
            _money(photo_subtotal)
        ),

        "frame_subtotal": float(
            _money(frame_subtotal)
        ),

        "total": float(
            _money(total)
        ),
    }


# ============================================================
# PASSPORT PHOTO
# ============================================================

PASSPORT_PHOTO_PRICE = Decimal("10.00")


def compute_passport_photo_price(quantity):
    """
    Server-side price calculation for passport photos.

    Price:
        Rs. 10 per copy

    Quantity:
        1 to 12
    """

    quantity = max(
        1,
        min(12, int(quantity or 1))
    )

    total = (
        PASSPORT_PHOTO_PRICE
        * quantity
    )

    return {
        "quantity": quantity,

        "price_per_copy": float(
            _money(PASSPORT_PHOTO_PRICE)
        ),

        "total": float(
            _money(total)
        ),
    }


# ============================================================
# CART TOTALS
# ============================================================

def compute_cart_totals(cart):
    """Calculate subtotal, delivery charge and minimum order status."""

    subtotal = Decimal("0")

    for item in cart.items:
        subtotal += Decimal(
            str(item.line_total())
        )

    min_order = Decimal(
        str(
            Setting.get_float(
                "minimum_order_value",
                100
            )
        )
    )

    free_delivery_threshold = Decimal(
        str(
            Setting.get_float(
                "free_delivery_threshold",
                100
            )
        )
    )

    delivery_charge_setting = Decimal(
        str(
            Setting.get_float(
                "delivery_charge",
                30
            )
        )
    )

    if subtotal >= free_delivery_threshold:
        delivery_charge = Decimal("0")
    else:
        delivery_charge = delivery_charge_setting

    return {
        "subtotal": float(
            _money(subtotal)
        ),

        "delivery_charge": float(
            _money(delivery_charge)
        ),

        "minimum_order_value": float(
            _money(min_order)
        ),

        "meets_minimum_order": (
            subtotal >= min_order
        ),

        "free_delivery_threshold": float(
            _money(free_delivery_threshold)
        ),
    }


# ============================================================
# COUPONS
# ============================================================

def apply_coupon(coupon, subtotal):
    """Validate and calculate coupon discount."""

    subtotal = Decimal(str(subtotal))

    if coupon is None:
        return (
            False,
            Decimal("0"),
            "Invalid coupon code."
        )

    if not coupon.is_valid_now():
        return (
            False,
            Decimal("0"),
            "This coupon is inactive or has expired."
        )

    if subtotal < Decimal(
        str(coupon.minimum_order_value or 0)
    ):
        return (
            False,
            Decimal("0"),
            (
                f"Minimum order of Rs. "
                f"{coupon.minimum_order_value} "
                f"required for this coupon."
            )
        )

    if coupon.discount_type == "PERCENT":
        discount = (
            subtotal
            * Decimal(str(coupon.discount_value))
            / Decimal("100")
        )

        if coupon.maximum_discount is not None:
            discount = min(
                discount,
                Decimal(str(coupon.maximum_discount))
            )

    else:
        # FIXED
        discount = Decimal(
            str(coupon.discount_value)
        )

    discount = min(
        discount,
        subtotal
    )

    return (
        True,
        _money(discount),
        "Coupon applied successfully."
    )


# ============================================================
# ORDER SUMMARY
# ============================================================

def compute_order_summary(
    cart,
    coupon=None,
):
    """Full checkout-time summary."""

    totals = compute_cart_totals(cart)

    subtotal = Decimal(
        str(totals["subtotal"])
    )

    delivery_charge = Decimal(
        str(totals["delivery_charge"])
    )

    discount = Decimal("0")
    coupon_message = None

    if coupon is not None:
        valid, discount, coupon_message = apply_coupon(
            coupon,
            subtotal
        )

        if not valid:
            discount = Decimal("0")

    total = (
        subtotal
        + delivery_charge
        - discount
    )

    if total < 0:
        total = Decimal("0")

    return {
        "subtotal": float(
            _money(subtotal)
        ),

        "delivery_charge": float(
            _money(delivery_charge)
        ),

        "discount_amount": float(
            _money(discount)
        ),

        "total_amount": float(
            _money(total)
        ),

        "coupon_message": coupon_message,
    }