from flask import Blueprint, render_template, request, session

from models import Category, PrintingService, StationeryProduct
from utils import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def onboarding():
    if current_user():
        return render_template("customer/home.html", **home_context())
    if session.get("seen_onboarding"):
        return render_template("customer/home.html", **home_context())
    return render_template("customer/onboarding.html")


@main_bp.route("/home")
def home():
    session["seen_onboarding"] = True
    return render_template("customer/home.html", **home_context())


def home_context():
    printing_categories = Category.query.filter_by(
        kind="printing",
        is_active=True
    ).order_by(Category.sort_order).all()

    stationery_categories = Category.query.filter_by(
        kind="stationery",
        is_active=True
    ).order_by(Category.sort_order).all()

    popular_printing = PrintingService.query.filter_by(
        is_active=True
    ).limit(7).all()

    popular_stationery = StationeryProduct.query.filter_by(
        is_active=True
    ).limit(8).all()

    return {
        "printing_categories": printing_categories,
        "stationery_categories": stationery_categories,
        "popular_printing": popular_printing,
        "popular_stationery": popular_stationery,
    }

@main_bp.route("/categories")
def categories():
    printing_categories = Category.query.filter_by(kind="printing", is_active=True).order_by(Category.sort_order).all()
    stationery_categories = Category.query.filter_by(kind="stationery", is_active=True).order_by(Category.sort_order).all()
    return render_template("customer/categories.html",
                            printing_categories=printing_categories,
                            stationery_categories=stationery_categories)


@main_bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    services, products = [], []
    if q:
        like = f"%{q}%"
        services = PrintingService.query.filter(PrintingService.is_active == True,
                                                  PrintingService.name.ilike(like)).all()
        products = StationeryProduct.query.filter(StationeryProduct.is_active == True,
                                                    StationeryProduct.name.ilike(like)).all()
    return render_template("customer/categories.html", search_query=q,
                            search_services=services, search_products=products,
                            printing_categories=[], stationery_categories=[])
