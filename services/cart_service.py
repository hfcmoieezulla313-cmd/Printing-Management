
"""
Cart manipulation helpers.

Printing, photo, and passport-photo cart logic.
"""

from models import (
    db,
    Cart,
    CartItem,
    PrintConfiguration,
    PhotoConfiguration,
)

from services.pricing_service import compute_print_price


def get_or_create_cart(user):
    """Return the user's existing cart or create one."""

    if user.cart:
        return user.cart

    cart = Cart(user_id=user.id)
    db.session.add(cart)
    db.session.commit()

    return cart


def add_printing_item_to_cart(
    user,
    document,
    printing_service,
    paper_size,
    print_type,
    print_side,
    copies,
    binding,
    page_count,
):
    """Create a printing configuration and add it to the cart."""

    cart = get_or_create_cart(user)

    breakdown = compute_print_price(
        printing_service,
        paper_size,
        print_type,
        print_side,
        copies,
        binding,
        page_count,
    )

    config = PrintConfiguration(
        document_id=document.id,
        printing_service_id=printing_service.id,
        paper_size=paper_size,
        print_type=print_type,
        print_side=print_side,
        copies=copies,
        binding=binding,
        page_count=page_count,
        computed_total=breakdown["total"],
    )

    db.session.add(config)
    db.session.flush()

    item = CartItem(
        cart_id=cart.id,
        item_type="PRINTING",
        print_configuration_id=config.id,
        quantity=1,
        unit_price=breakdown["total"],
    )

    db.session.add(item)
    db.session.commit()

    return item


def add_photo_item_to_cart(
    user,
    document,
    photo_size,
    frame,
    quantity,
    computed_total,
):
    """Create a PHOTO configuration and add it to the cart."""

    cart = get_or_create_cart(user)

    quantity = max(1, min(100, int(quantity)))

    config = PhotoConfiguration(
        document_id=document.id,
        photo_type="PHOTO",
        photo_size=photo_size,
        frame=frame,
        quantity=quantity,
        computed_total=computed_total,
    )

    db.session.add(config)
    db.session.flush()

    item = CartItem(
        cart_id=cart.id,
        item_type="PHOTO",
        photo_configuration_id=config.id,
        quantity=1,
        unit_price=computed_total,
    )

    db.session.add(item)
    db.session.commit()

    return item


def add_passport_photo_item_to_cart(
    user,
    document,
    quantity,
    computed_total,
):
    """Create a PASSPORT photo configuration and add it to the cart."""

    cart = get_or_create_cart(user)

    quantity = max(1, min(12, int(quantity)))

    config = PhotoConfiguration(
        document_id=document.id,
        photo_type="PASSPORT",
        photo_size=None,
        frame=None,
        quantity=quantity,
        computed_total=computed_total,
    )

    db.session.add(config)
    db.session.flush()

    item = CartItem(
        cart_id=cart.id,
        item_type="PASSPORT",
        photo_configuration_id=config.id,
        quantity=1,
        unit_price=computed_total,
    )

    db.session.add(item)
    db.session.commit()

    return item


def update_cart_item_quantity(user, item_id, quantity):
    """Update the quantity of a cart item or remove it."""

    item = CartItem.query.join(Cart).filter(
        CartItem.id == item_id,
        Cart.user_id == user.id,
    ).first()

    if not item:
        return None

    quantity = int(quantity)

    if quantity <= 0:
        db.session.delete(item)
        db.session.commit()
        return None

    # Printing, photo and passport configurations are priced
    # individually, so their cart-item quantity remains 1.
    if item.item_type not in ("PRINTING", "PHOTO", "PASSPORT"):
        return None

    item.quantity = 1
    db.session.commit()

    return item


def remove_cart_item(user, item_id):
    """Remove one cart item belonging to the current user."""

    item = CartItem.query.join(Cart).filter(
        CartItem.id == item_id,
        Cart.user_id == user.id,
    ).first()

    if item:
        db.session.delete(item)
        db.session.commit()
        return True

    return False


def clear_cart(user):
    """Remove all items from the user's cart."""

    cart = get_or_create_cart(user)

    for item in list(cart.items):
        db.session.delete(item)

    db.session.commit()
