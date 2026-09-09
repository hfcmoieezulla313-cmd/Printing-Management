from flask import Blueprint, render_template, request, jsonify

from models import PrintingService, Category
from services.pricing_service import compute_print_price
from utils import login_required

printing_bp = Blueprint("printing", __name__, url_prefix="/printing")


@printing_bp.route("/")
def list_services():
    category_id = request.args.get("category", type=int)
    query = PrintingService.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    services = query.all()
    categories = Category.query.filter_by(kind="printing", is_active=True).order_by(Category.sort_order).all()
    return render_template("customer/printing.html", services=services, categories=categories,
                            active_category=category_id)


@printing_bp.route("/<slug>")
def details(slug):
    service = PrintingService.query.filter_by(slug=slug, is_active=True).first_or_404()
    return render_template("customer/printing_details.html", service=service)


@printing_bp.route("/api/quote", methods=["POST"])
@login_required
def quote():
    """Server-side live price preview used by the configuration screen's
    JavaScript. The client sends only choices, never prices."""
    data = request.get_json(force=True) or {}
    service = PrintingService.query.get_or_404(data.get("printing_service_id"))
    breakdown = compute_print_price(
        service,
        data.get("paper_size", "A4"),
        data.get("print_type", "BW"),
        data.get("print_side", "SINGLE"),
        data.get("copies", 1),
        data.get("binding", "NONE"),
        data.get("page_count", 1),
    )
    return jsonify(breakdown)
