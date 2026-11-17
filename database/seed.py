
"""
Printify Database Setup + Seed Script

Run from project root:

    python database/seed.py

This script:
1. Creates database tables if they do not exist.
2. Seeds application settings.
3. Seeds printing categories.
4. Seeds printing services.
5. Seeds coupons.
6. Creates the initial admin account.

Stationery functionality has been removed.
"""

import os
import sys

# ============================================================
# PROJECT PATH
# ============================================================

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from app import create_app

from models import (
    db,
    Category,
    PrintingService,
    Coupon,
    Setting,
    Admin
)

app = create_app()


# ============================================================
# SETTINGS
# ============================================================

def seed_settings():

    defaults = {
        "minimum_order_value": (
            "100",
            "Minimum order value (Rs.)"
        ),
        "free_delivery_threshold": (
            "100",
            "Free delivery threshold (Rs.)"
        ),
        "delivery_charge": (
            "30",
            "Delivery charge below threshold (Rs.)"
        ),
        "spiral_binding_price": (
            "20",
            "Spiral binding price (Rs.) per copy"
        ),
        "support_phone": (
            "1800-000-0000",
            "Support phone number"
        ),
        "support_email": (
            "support@printcare.local",
            "Support email"
        ),
        "application_name": (
            "Printify",
            "Application display name"
        ),
    }

    for key, (value, description) in defaults.items():

        existing = Setting.query.filter_by(
            key=key
        ).first()

        if not existing:
            db.session.add(
                Setting(
                    key=key,
                    value=value,
                    description=description
                )
            )

    db.session.commit()
    print("Settings seeded.")


# ============================================================
# PRINTING CATEGORIES
# ============================================================

def seed_categories():

    printing_categories = [
        "B&W Print",
        "Color Print",
        "Photocopy",
        "Scan",
        "Binding",
        "Design & Print"
    ]

    created = {}

    for index, name in enumerate(printing_categories):

        category = Category.query.filter_by(
            name=name,
            kind="printing"
        ).first()

        if not category:

            category = Category(
                name=name,
                kind="printing",
                sort_order=index,
                icon="printer",
                is_active=True
            )

            db.session.add(category)

        else:

            category.sort_order = index
            category.icon = "printer"
            category.is_active = True

        created[name] = category

    db.session.commit()

    print("Printing categories seeded.")

    return created


# ============================================================
# PRINTING SERVICES
# ============================================================

def seed_printing_services(categories):

    bw = categories["B&W Print"]
    color = categories["Color Print"]
    binding = categories["Binding"]
    scan = categories["Scan"]

    services = [

        {
            "name": "A4 B&W Print",
            "slug": "a4-bw-print",
            "category": bw,
            "paper_size": "A4",
            "print_type": "BW",
            "price_per_page": 1,
            "double_side_extra": 0,
            "is_configurable": True,
            "description":
                "Crisp black and white printing on A4 paper."
        },

        {
            "name": "A4 Color Print",
            "slug": "a4-color-print",
            "category": color,
            "paper_size": "A4",
            "print_type": "COLOR",
            "price_per_page": 5,
            "double_side_extra": 1,
            "is_configurable": True,
            "description":
                "High-quality colour printing on A4 paper."
        },

        {
            "name": "A3 B&W Print",
            "slug": "a3-bw-print",
            "category": bw,
            "paper_size": "A3",
            "print_type": "BW",
            "price_per_page": 2,
            "double_side_extra": 0,
            "is_configurable": True,
            "description":
                "Black and white printing on large A3 paper."
        },

        {
            "name": "A3 Color Print",
            "slug": "a3-color-print",
            "category": color,
            "paper_size": "A3",
            "print_type": "COLOR",
            "price_per_page": 10,
            "double_side_extra": 2,
            "is_configurable": True,
            "description":
                "Full colour printing on large A3 paper."
        },

        {
            "name": "Double Side Print",
            "slug": "double-side-print",
            "category": bw,
            "paper_size": "A4",
            "print_type": "BW",
            "price_per_page": 2,
            "double_side_extra": 0,
            "is_configurable": True,
            "description":
                "Double-sided printing to reduce paper usage."
        },

        {
            "name": "Spiral Binding",
            "slug": "spiral-binding",
            "category": binding,
            "paper_size": None,
            "print_type": None,
            "price_per_page": 0,
            "double_side_extra": 0,
            "is_configurable": False,
            "flat_price": 20,
            "description":
                "Professional spiral binding for documents and projects."
        },

        {
            "name": "Scanning",
            "slug": "scanning",
            "category": scan,
            "paper_size": "A4",
            "print_type": None,
            "price_per_page": 5,
            "double_side_extra": 0,
            "is_configurable": True,
            "description":
                "High-quality document scanning to PDF or JPG."
        }
    ]

    for service in services:

        existing = PrintingService.query.filter_by(
            slug=service["slug"]
        ).first()

        if existing:

            existing.name = service["name"]
            existing.category_id = service["category"].id
            existing.description = service["description"]
            existing.paper_size = service.get("paper_size")
            existing.print_type = service.get("print_type")
            existing.price_per_page = service.get(
                "price_per_page", 0
            )
            existing.double_side_extra = service.get(
                "double_side_extra", 0
            )
            existing.is_configurable = service.get(
                "is_configurable", True
            )
            existing.flat_price = service.get("flat_price")

        else:

            db.session.add(
                PrintingService(
                    name=service["name"],
                    slug=service["slug"],
                    category_id=service["category"].id,
                    description=service["description"],
                    paper_size=service.get("paper_size"),
                    print_type=service.get("print_type"),
                    price_per_page=service.get(
                        "price_per_page", 0
                    ),
                    double_side_extra=service.get(
                        "double_side_extra", 0
                    ),
                    is_configurable=service.get(
                        "is_configurable", True
                    ),
                    flat_price=service.get("flat_price")
                )
            )

    db.session.commit()

    print("Printing services seeded.")


# ============================================================
# COUPONS
# ============================================================

def seed_coupons():

    welcome = Coupon.query.filter_by(
        code="WELCOME50"
    ).first()

    if not welcome:

        db.session.add(
            Coupon(
                code="WELCOME50",
                discount_type="PERCENT",
                discount_value=50,
                minimum_order_value=100,
                maximum_discount=50,
                active=True
            )
        )

    flat = Coupon.query.filter_by(
        code="FLAT20"
    ).first()

    if not flat:

        db.session.add(
            Coupon(
                code="FLAT20",
                discount_type="FIXED",
                discount_value=20,
                minimum_order_value=150,
                active=True
            )
        )

    db.session.commit()

    print("Coupons seeded.")


# ============================================================
# ADMIN
# ============================================================

def seed_admin():

    username = os.environ.get(
        "INITIAL_ADMIN_USERNAME",
        "admin"
    )

    password = os.environ.get(
        "INITIAL_ADMIN_PASSWORD",
        "change_me_admin_password"
    )

    email = os.environ.get(
        "INITIAL_ADMIN_EMAIL",
        "admin@printcare.local"
    )

    existing = Admin.query.filter_by(
        username=username
    ).first()

    if existing:

        print(
            f"Admin '{username}' already exists - skipping."
        )

        return

    admin = Admin(
        username=username,
        email=email
    )

    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    print(
        f"Initial admin account created. Username: {username}"
    )

    print(
        "IMPORTANT: Change the admin password after login."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    with app.app_context():

        db.create_all()

        print(
            "Tables created (if they did not already exist)."
        )

        seed_settings()

        categories = seed_categories()

        seed_printing_services(categories)

        seed_coupons()

        seed_admin()

        print()
        print("==========================================")
        print("       PRINTIFY SEEDING COMPLETE")
        print("==========================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
