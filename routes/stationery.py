from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import StationeryProduct, Category
from services.cart_service import add_stationery_item_to_cart
from utils import login_required, current_user

stationery_bp = Blueprint("stationery", __name__, url_prefix="/stationery")


@stationery_bp.route("/")
def list_products():
    category_id = request.args.get("category", type=int)
    query = StationeryProduct.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    products = query.all()
    categories = Category.query.filter_by(kind="stationery", is_active=True).order_by(Category.sort_order).all()
    return render_template("customer/stationery.html", products=products, categories=categories,
                            active_category=category_id)


@stationery_bp.route("/<int:product_id>")
def details(product_id):
    product = StationeryProduct.query.filter_by(id=product_id, is_active=True).first_or_404()
    return render_template("customer/product_details.html", product=product)


@stationery_bp.route("/<int:product_id>/add-to-cart", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = StationeryProduct.query.filter_by(id=product_id, is_active=True).first_or_404()
    quantity = request.form.get("quantity", 1, type=int) or 1
    if not product.in_stock():
        flash("Sorry, this item is out of stock.", "danger")
        return redirect(url_for("stationery.details", product_id=product_id))
    add_stationery_item_to_cart(current_user(), product, quantity)
    flash(f"{product.name} added to cart.", "success")
    return redirect(url_for("cart.view_cart"))
