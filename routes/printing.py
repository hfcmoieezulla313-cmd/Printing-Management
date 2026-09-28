from flask import Blueprint, render_template, request, jsonify

from models import PrintingService, Category
from services.pricing_service import compute_print_price
from utils import login_required


printing_bp = Blueprint(
    "printing",
    __name__,
    url_prefix="/printing"
)


# =========================================================
# PRINTING SERVICES
# =========================================================

@printing_bp.route("/")
def list_services():

    category_id = request.args.get(
        "category",
        type=int
    )

    query = PrintingService.query.filter_by(
        is_active=True
    )

    if category_id:
        query = query.filter_by(
            category_id=category_id
        )

    services = query.all()

    categories = (
        Category.query
        .filter_by(
            kind="printing",
            is_active=True
        )
        .order_by(Category.sort_order)
        .all()
    )

    return render_template(
        "customer/printing.html",
        services=services,
        categories=categories,
        active_category=category_id
    )


# =========================================================
# PRINTING SERVICE DETAILS
# =========================================================

@printing_bp.route("/<slug>")
def details(slug):

    service = (
        PrintingService.query
        .filter_by(
            slug=slug,
            is_active=True
        )
        .first_or_404()
    )

    return render_template(
        "customer/printing_details.html",
        service=service
    )


# =========================================================
# SERVER-SIDE PRICE QUOTE
# =========================================================

@printing_bp.route(
    "/api/quote",
    methods=["POST"]
)
@login_required
def quote():

    """
    Server-side live price preview.

    The browser sends only printing choices.
    The server finds the correct active printing
    service from paper size + print type and
    calculates the price.
    """

    data = request.get_json(
        force=True
    ) or {}

    # -----------------------------------------------------
    # Read user choices
    # -----------------------------------------------------

    paper_size = (
        data.get("paper_size", "A4")
        or "A4"
    ).upper()

    print_type = (
        data.get("print_type", "BW")
        or "BW"
    ).upper()

    print_side = (
        data.get("print_side", "SINGLE")
        or "SINGLE"
    ).upper()

    binding = (
        data.get("binding", "NONE")
        or "NONE"
    ).upper()

    try:
        copies = int(
            data.get("copies", 1) or 1
        )
    except (TypeError, ValueError):
        copies = 1

    try:
        page_count = int(
            data.get("page_count", 1) or 1
        )
    except (TypeError, ValueError):
        page_count = 1

    copies = max(
        1,
        copies
    )

    page_count = max(
        1,
        page_count
    )

    # -----------------------------------------------------
    # Validate choices
    # -----------------------------------------------------

    if paper_size not in {
        "A4",
        "A3"
    }:
        return jsonify({
            "error": "Invalid paper size."
        }), 400

    if print_type not in {
        "BW",
        "COLOR"
    }:
        return jsonify({
            "error": "Invalid print type."
        }), 400

    if print_side not in {
        "SINGLE",
        "DOUBLE"
    }:
        return jsonify({
            "error": "Invalid print side."
        }), 400

    if binding not in {
        "NONE",
        "SPIRAL"
    }:
        return jsonify({
            "error": "Invalid binding option."
        }), 400

    # -----------------------------------------------------
    # Find the correct service dynamically.
    #
    # Example:
    # A4 + BW
    # A4 + COLOR
    # A3 + BW
    # A3 + COLOR
    # -----------------------------------------------------

    service = (
        PrintingService.query
        .filter_by(
            paper_size=paper_size,
            print_type=print_type,
            is_active=True
        )
        .first()
    )

    if not service:

        return jsonify({
            "error": (
                f"No printing service is available for "
                f"{paper_size} "
                f"{'Color' if print_type == 'COLOR' else 'B&W'}."
            )
        }), 404

    # -----------------------------------------------------
    # Calculate price on server.
    # -----------------------------------------------------

    breakdown = compute_print_price(
        service,
        paper_size,
        print_type,
        print_side,
        copies,
        binding,
        page_count
    )

    # Include the actual service ID for debugging/use
    # by the frontend, although the frontend does not
    # control the price.
    breakdown["printing_service_id"] = service.id

    return jsonify(
        breakdown
    )