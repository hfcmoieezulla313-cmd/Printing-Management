from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from services.cart_service import (get_or_create_cart, update_cart_item_quantity, remove_cart_item)
from services.pricing_service import compute_cart_totals
from utils import login_required, current_user

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


@cart_bp.route("/")
@login_required
def view_cart():
    user = current_user()
    cart = get_or_create_cart(user)
    totals = compute_cart_totals(cart)
    return render_template("customer/cart.html", cart=cart, totals=totals)


@cart_bp.route("/update/<int:item_id>", methods=["POST"])
@login_required
def update_item(item_id):
    quantity = request.form.get("quantity", 1, type=int) or 0
    update_cart_item_quantity(current_user(), item_id, quantity)
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_item(item_id):
    remove_cart_item(current_user(), item_id)
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/count")
@login_required
def item_count():
    cart = get_or_create_cart(current_user())
    return jsonify({"count": len(cart.items)})
