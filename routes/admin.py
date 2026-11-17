
from datetime import datetime

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)
from sqlalchemy import func

from models import (
    db, Admin, User, Order, PrintingService,
    Category, Coupon, Complaint, Setting
)

from services.order_service import (
    update_order_status,
    advance_order_status_if_due
)

from models.order import ORDER_STATUSES
from utils import admin_required, current_admin


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_admin():
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):

            session.clear()
            session["admin_id"] = admin.id

            return redirect(url_for("admin.dashboard"))

        flash("Invalid admin credentials.", "danger")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():

    session.pop("admin_id", None)

    return redirect(url_for("admin.login"))


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():

    all_orders = Order.query.all()

    for order in all_orders:
        advance_order_status_if_due(order)

    stats = {
        "total_orders": Order.query.count(),

        "pending_orders": Order.query.filter(
            Order.status.in_([
                "Pending",
                "Confirmed",
                "Printing",
                "Ready for Delivery",
                "Out for Delivery"
            ])
        ).count(),

        "completed_orders": Order.query.filter_by(
            status="Delivered"
        ).count(),

        "total_customers": User.query.count(),

        "total_services": PrintingService.query.count(),

        "total_revenue": db.session.query(
            func.coalesce(func.sum(Order.total_amount), 0)
        ).filter(
            Order.status != "Cancelled"
        ).scalar(),
    }

    recent_orders = Order.query.order_by(
        Order.created_at.desc()
    ).limit(8).all()

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_orders=recent_orders
    )


# ---------------------------------------------------------
# ORDERS
# ---------------------------------------------------------

@admin_bp.route("/orders")
@admin_required
def orders():

    status_filter = request.args.get("status")

    query = Order.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    order_list = query.order_by(
        Order.created_at.desc()
    ).all()

    for order in order_list:
        advance_order_status_if_due(order)

    return render_template(
        "admin/orders.html",
        orders=order_list,
        statuses=ORDER_STATUSES,
        active_status=status_filter
    )


@admin_bp.route("/orders/<order_number>")
@admin_required
def order_details(order_number):

    order = Order.query.filter_by(
        order_number=order_number
    ).first_or_404()

    advance_order_status_if_due(order)

    return render_template(
        "admin/order_details.html",
        order=order,
        statuses=ORDER_STATUSES
    )


# ---------------------------------------------------------
# UPDATE ORDER STATUS
# ---------------------------------------------------------

@admin_bp.route(
    "/orders/<order_number>/status",
    methods=["POST"]
)
@admin_required
def update_status(order_number):

    order = Order.query.filter_by(
        order_number=order_number
    ).first_or_404()

    new_status = request.form.get("status", "").strip()

    allowed_transitions = {
        "Ready for Delivery": ["Out for Delivery"],
        "Out for Delivery": ["Delivered"],
    }

    try:

        advance_order_status_if_due(order)

        allowed = allowed_transitions.get(order.status, [])

        if new_status not in allowed:
            raise ValueError(
                "This status change is not allowed. "
                "Please follow the order processing steps."
            )

        update_order_status(order, new_status)

        if new_status == "Out for Delivery":
            flash(
                "Order has been sent for delivery. Customer notified.",
                "success"
            )

        elif new_status == "Delivered":
            flash(
                "Order marked as delivered. Customer notified.",
                "success"
            )

    except ValueError as e:
        flash(str(e), "danger")

    return redirect(
        url_for(
            "admin.order_details",
            order_number=order_number
        )
    )


# ---------------------------------------------------------
# CUSTOMERS
# ---------------------------------------------------------

@admin_bp.route("/customers")
@admin_required
def customers():

    user_list = User.query.order_by(
        User.created_at.desc()
    ).all()

    return render_template(
        "admin/customers.html",
        customers=user_list
    )


# ---------------------------------------------------------
# CUSTOMER DETAILS AND ORDER HISTORY
# ---------------------------------------------------------

@admin_bp.route("/customers/<int:user_id>")
@admin_required
def customer_details(user_id):

    customer = User.query.get_or_404(user_id)

    customer_orders = list(customer.orders)

    for order in customer_orders:
        advance_order_status_if_due(order)

    customer_orders.sort(
        key=lambda order: order.created_at or datetime.min,
        reverse=True
    )

    total_orders = len(customer_orders)

    total_spent = sum(
        float(order.total_amount or 0)
        for order in customer_orders
        if order.status != "Cancelled"
    )

    return render_template(
        "admin/customer_details.html",
        customer=customer,
        orders=customer_orders,
        total_orders=total_orders,
        total_spent=total_spent
    )


# ---------------------------------------------------------
# CATEGORIES - PRINTING ONLY
# ---------------------------------------------------------

@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories():

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if not name:
            flash("Please enter a category name.", "danger")
            return redirect(url_for("admin.categories"))

        category = Category(
            name=name,
            kind="printing",
            icon=request.form.get("icon", "folder").strip() or "folder",
            sort_order=request.form.get("sort_order", 0, type=int),
        )

        db.session.add(category)
        db.session.commit()

        flash("Printing category created successfully.", "success")

        return redirect(url_for("admin.categories"))

    category_list = Category.query.filter_by(
        kind="printing"
    ).order_by(
        Category.sort_order
    ).all()

    return render_template(
        "admin/categories.html",
        categories=category_list
    )


@admin_bp.route(
    "/categories/<int:category_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_category(category_id):

    category = Category.query.filter_by(
        id=category_id,
        kind="printing"
    ).first_or_404()

    db.session.delete(category)
    db.session.commit()

    flash("Printing category deleted.", "info")

    return redirect(url_for("admin.categories"))


# ---------------------------------------------------------
# PRINTING SERVICES
# ---------------------------------------------------------

@admin_bp.route("/printing-services", methods=["GET", "POST"])
@admin_required
def printing_services():

    if request.method == "POST":

        service_id = request.form.get("id", type=int)

        service = (
            PrintingService.query.get(service_id)
            if service_id else PrintingService()
        )

        service.name = request.form.get("name", "").strip()

        service.slug = (
            request.form.get("slug", "")
            .strip()
            .lower()
            .replace(" ", "-")
        )

        service.category_id = request.form.get(
            "category_id", type=int
        )

        service.description = request.form.get(
            "description", ""
        ).strip()

        service.paper_size = request.form.get("paper_size") or None
        service.print_type = request.form.get("print_type") or None

        service.price_per_page = request.form.get(
            "price_per_page", 0, type=float
        )

        service.double_side_extra = request.form.get(
            "double_side_extra", 0, type=float
        )

        service.is_configurable = (
            request.form.get("is_configurable") == "on"
        )

        flat_price = request.form.get("flat_price")

        service.flat_price = (
            float(flat_price) if flat_price else None
        )

        service.is_active = (
            request.form.get("is_active") == "on"
        )

        if not service_id:
            db.session.add(service)

        db.session.commit()

        flash("Printing service saved.", "success")

        return redirect(url_for("admin.printing_services"))

    services = PrintingService.query.order_by(
        PrintingService.name
    ).all()

    categories = Category.query.filter_by(
        kind="printing"
    ).all()

    return render_template(
        "admin/printing_services.html",
        services=services,
        categories=categories
    )


@admin_bp.route(
    "/printing-services/<int:service_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_printing_service(service_id):

    service = PrintingService.query.get_or_404(service_id)

    db.session.delete(service)
    db.session.commit()

    flash("Printing service deleted.", "info")

    return redirect(url_for("admin.printing_services"))


# ---------------------------------------------------------
# COUPONS
# ---------------------------------------------------------

@admin_bp.route("/coupons", methods=["GET", "POST"])
@admin_required
def coupons():

    if request.method == "POST":

        coupon_id = request.form.get("id", type=int)

        coupon = (
            Coupon.query.get(coupon_id)
            if coupon_id else Coupon()
        )

        coupon.code = request.form.get(
            "code", ""
        ).strip().upper()

        coupon.discount_type = request.form.get(
            "discount_type", "PERCENT"
        )

        coupon.discount_value = request.form.get(
            "discount_value", 0, type=float
        )

        coupon.minimum_order_value = request.form.get(
            "minimum_order_value", 0, type=float
        )

        max_discount = request.form.get("maximum_discount")

        coupon.maximum_discount = (
            float(max_discount) if max_discount else None
        )

        coupon.active = request.form.get("active") == "on"

        expiry = request.form.get("expiry_date")
        coupon.expiry_date = expiry or None

        if not coupon_id:
            db.session.add(coupon)

        db.session.commit()

        flash("Coupon saved.", "success")

        return redirect(url_for("admin.coupons"))

    coupon_list = Coupon.query.order_by(
        Coupon.created_at.desc()
    ).all()

    return render_template(
        "admin/coupons.html",
        coupons=coupon_list
    )


@admin_bp.route(
    "/coupons/<int:coupon_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_coupon(coupon_id):

    coupon = Coupon.query.get_or_404(coupon_id)

    db.session.delete(coupon)
    db.session.commit()

    flash("Coupon deleted.", "info")

    return redirect(url_for("admin.coupons"))


# ---------------------------------------------------------
# COMPLAINTS
# ---------------------------------------------------------

@admin_bp.route("/complaints")
@admin_required
def complaints():

    complaint_list = Complaint.query.order_by(
        Complaint.created_at.desc()
    ).all()

    return render_template(
        "admin/complaints.html",
        complaints=complaint_list
    )


@admin_bp.route(
    "/complaints/<int:complaint_id>/status",
    methods=["POST"]
)
@admin_required
def update_complaint_status(complaint_id):

    complaint = Complaint.query.get_or_404(complaint_id)

    complaint.status = request.form.get(
        "status", complaint.status
    )

    db.session.commit()

    flash("Complaint updated.", "success")

    return redirect(url_for("admin.complaints"))


# ---------------------------------------------------------
# REPORTS
# ---------------------------------------------------------

@admin_bp.route("/reports")
@admin_required
def reports():

    revenue_by_status = (
        db.session.query(
            Order.status,
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), 0)
        )
        .group_by(Order.status)
        .all()
    )

    return render_template(
        "admin/reports.html",
        revenue_by_status=revenue_by_status
    )


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

SETTINGS_FIELDS = [
    ("minimum_order_value", "Minimum order value (Rs.)"),
    ("free_delivery_threshold", "Free delivery threshold (Rs.)"),
    ("delivery_charge", "Delivery charge (Rs.)"),
    ("spiral_binding_price", "Spiral binding price (Rs.)"),
    ("support_phone", "Support phone"),
    ("support_email", "Support email"),
    ("application_name", "Application name"),
]


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():

    if request.method == "POST":

        for key, label in SETTINGS_FIELDS:

            value = request.form.get(key, "")

            Setting.set(key, value, label)

        db.session.commit()

        flash("Settings updated.", "success")

        return redirect(url_for("admin.settings"))

    current_values = {
        key: Setting.get(key, "")
        for key, _ in SETTINGS_FIELDS
    }

    return render_template(
        "admin/settings.html",
        fields=SETTINGS_FIELDS,
        values=current_values
    )
