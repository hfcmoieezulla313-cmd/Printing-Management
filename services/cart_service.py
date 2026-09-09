"""Cart manipulation helpers - kept out of routes/cart.py so the route
stays thin and this logic is reusable/testable."""
from models import db, Cart, CartItem, PrintConfiguration, StationeryProduct
from services.pricing_service import compute_print_price


def get_or_create_cart(user):
    if user.cart:
        return user.cart
    cart = Cart(user_id=user.id)
    db.session.add(cart)
    db.session.commit()
    return cart


def add_printing_item_to_cart(user, document, printing_service, paper_size, print_type,
                               print_side, copies, binding, page_count):
    cart = get_or_create_cart(user)
    breakdown = compute_print_price(printing_service, paper_size, print_type, print_side,
                                     copies, binding, page_count)

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
    db.session.flush()  # get config.id without a full commit

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


def add_stationery_item_to_cart(user, product: StationeryProduct, quantity=1):
    cart = get_or_create_cart(user)
    quantity = max(1, int(quantity))

    existing = CartItem.query.filter_by(
        cart_id=cart.id, item_type="STATIONERY", stationery_product_id=product.id
    ).first()
    if existing:
        existing.quantity += quantity
        db.session.commit()
        return existing

    item = CartItem(
        cart_id=cart.id,
        item_type="STATIONERY",
        stationery_product_id=product.id,
        quantity=quantity,
        unit_price=product.price,
    )
    db.session.add(item)
    db.session.commit()
    return item


def update_cart_item_quantity(user, item_id, quantity):
    item = CartItem.query.join(Cart).filter(
        CartItem.id == item_id, Cart.user_id == user.id
    ).first()
    if not item:
        return None
    quantity = int(quantity)
    if quantity <= 0:
        db.session.delete(item)
        db.session.commit()
        return None
    if item.item_type == "STATIONERY":
        item.quantity = quantity
    db.session.commit()
    return item


def remove_cart_item(user, item_id):
    item = CartItem.query.join(Cart).filter(
        CartItem.id == item_id, Cart.user_id == user.id
    ).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        return True
    return False


def clear_cart(user):
    cart = get_or_create_cart(user)
    for item in list(cart.items):
        db.session.delete(item)
    db.session.commit()
