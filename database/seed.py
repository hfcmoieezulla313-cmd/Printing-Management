"""
Database setup + seed script.

Run from the project root (after creating the MySQL database and
filling in .env):

    python database/seed.py

This will:
  1. Create all tables (via SQLAlchemy models) if they don't exist.
  2. Insert default application settings.
  3. Insert sample categories, printing services, stationery products,
     and a sample coupon.
  4. Create the initial admin account (from .env, or safe defaults),
     using secure password hashing.
  5. Add/update stationery product images.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import (
    db,
    Category,
    PrintingService,
    StationeryProduct,
    Coupon,
    Setting,
    Admin
)

app = create_app()


def seed_settings():
    defaults = {
        "minimum_order_value": ("100", "Minimum order value (Rs.)"),
        "free_delivery_threshold": ("100", "Free delivery threshold (Rs.)"),
        "delivery_charge": ("30", "Delivery charge below threshold (Rs.)"),
        "spiral_binding_price": ("20", "Spiral binding price (Rs.) per copy"),
        "support_phone": ("1800-000-0000", "Support phone number"),
        "support_email": ("support@printcare.local", "Support email"),
        "application_name": ("PrintCare", "Application display name"),
    }

    for key, (value, desc) in defaults.items():
        if not Setting.query.filter_by(key=key).first():
            db.session.add(
                Setting(
                    key=key,
                    value=value,
                    description=desc
                )
            )

    db.session.commit()
    print("Settings seeded.")


def seed_categories():
    printing_cats = [
        "B&W Print",
        "Color Print",
        "Photocopy",
        "Scan",
        "Binding",
        "Design & Print"
    ]

    stationery_cats = [
        "Pens & Pencils",
        "Notebooks",
        "Files & Folders",
        "Office Supplies"
    ]

    created = {}

    for i, name in enumerate(printing_cats):
        cat = Category.query.filter_by(
            name=name,
            kind="printing"
        ).first()

        if not cat:
            cat = Category(
                name=name,
                kind="printing",
                sort_order=i,
                icon="printer"
            )
            db.session.add(cat)

        created[("printing", name)] = cat

    for i, name in enumerate(stationery_cats):
        cat = Category.query.filter_by(
            name=name,
            kind="stationery"
        ).first()

        if not cat:
            cat = Category(
                name=name,
                kind="stationery",
                sort_order=i,
                icon="pen"
            )
            db.session.add(cat)

        created[("stationery", name)] = cat

    db.session.commit()

    print("Categories seeded.")

    return created


def seed_printing_services(categories):
    bw = categories[("printing", "B&W Print")]
    color = categories[("printing", "Color Print")]
    binding = categories[("printing", "Binding")]
    scan = categories[("printing", "Scan")]

    services = [
        dict(
            name="A4 B&W Print",
            slug="a4-bw-print",
            category=bw,
            paper_size="A4",
            print_type="BW",
            price_per_page=1,
            double_side_extra=0,
            is_configurable=True,
            description="Crisp black & white prints on standard A4 paper."
        ),

        dict(
            name="A4 Color Print",
            slug="a4-color-print",
            category=color,
            paper_size="A4",
            print_type="COLOR",
            price_per_page=5,
            double_side_extra=1,
            is_configurable=True,
            description="Vibrant full-color prints on standard A4 paper."
        ),

        dict(
            name="A3 B&W Print",
            slug="a3-bw-print",
            category=bw,
            paper_size="A3",
            print_type="BW",
            price_per_page=2,
            double_side_extra=0,
            is_configurable=True,
            description="Black & white prints on large A3 paper."
        ),

        dict(
            name="A3 Color Print",
            slug="a3-color-print",
            category=color,
            paper_size="A3",
            print_type="COLOR",
            price_per_page=10,
            double_side_extra=2,
            is_configurable=True,
            description="Full-color prints on large A3 paper."
        ),

        dict(
            name="Double Side Print",
            slug="double-side-print",
            category=bw,
            paper_size="A4",
            print_type="BW",
            price_per_page=2,
            double_side_extra=0,
            is_configurable=True,
            description="Double-sided printing to save paper."
        ),

        dict(
            name="Spiral Binding",
            slug="spiral-binding",
            category=binding,
            paper_size=None,
            print_type=None,
            price_per_page=0,
            is_configurable=False,
            flat_price=20,
            description="Durable spiral binding for your printed documents."
        ),

        dict(
            name="Scanning",
            slug="scanning",
            category=scan,
            paper_size="A4",
            print_type=None,
            price_per_page=5,
            is_configurable=True,
            description="High-quality document scanning to PDF/JPG."
        ),
    ]

    for s in services:
        existing = PrintingService.query.filter_by(
            slug=s["slug"]
        ).first()

        if existing:
            continue

        db.session.add(
            PrintingService(
                name=s["name"],
                slug=s["slug"],
                category_id=s["category"].id,
                description=s["description"],
                paper_size=s.get("paper_size"),
                print_type=s.get("print_type"),
                price_per_page=s.get("price_per_page", 0),
                double_side_extra=s.get("double_side_extra", 0),
                is_configurable=s.get("is_configurable", True),
                flat_price=s.get("flat_price"),
            )
        )

    db.session.commit()

    print("Printing services seeded.")


def seed_stationery(categories):
    pens = categories[("stationery", "Pens & Pencils")]
    notebooks = categories[("stationery", "Notebooks")]
    files = categories[("stationery", "Files & Folders")]
    office = categories[("stationery", "Office Supplies")]

    products = [
        dict(
            name="Blue Ballpoint Pen (Pack of 5)",
            category=pens,
            price=45,
            stock=200,
            image="images/stationery/pen.png",
            description="Smooth-writing blue ballpoint pens, pack of 5."
        ),

        dict(
            name="HB Pencil (Pack of 10)",
            category=pens,
            price=60,
            stock=150,
            image="images/stationery/pencil.png",
            description="Standard HB pencils for everyday writing."
        ),

        dict(
            name="A4 Ruled Notebook - 200 Pages",
            category=notebooks,
            price=90,
            stock=100,
            image="images/stationery/notebook.png",
            description="A4 size ruled notebook, 200 pages, sturdy binding."
        ),

        dict(
            name="Spiral Notebook - Pocket Size",
            category=notebooks,
            price=55,
            stock=120,
            image="images/stationery/spiral_notebook.png",
            description="Compact spiral notebook, perfect for notes on the go."
        ),

        dict(
            name="Plastic File Folder (Pack of 5)",
            category=files,
            price=120,
            stock=80,
            image="images/stationery/file_folder.png",
            description="Durable plastic file folders, pack of 5, assorted colors."
        ),

        dict(
            name="Ring Binder File",
            category=files,
            price=150,
            stock=60,
            image="images/stationery/binder.png",
            description="2-ring binder file for organizing loose documents."
        ),

        dict(
            name="Stapler with Pins",
            category=office,
            price=99,
            stock=70,
            image="images/stationery/stapler.png",
            description="Compact desktop stapler with a box of pins included."
        ),

        dict(
            name="Sticky Notes (Pack of 4)",
            category=office,
            price=70,
            stock=140,
            image="images/stationery/sticky_notes.png",
            description="Assorted color sticky notes, pack of 4 pads."
        ),
    ]

    for p in products:
        existing = StationeryProduct.query.filter_by(
            name=p["name"]
        ).first()

        if existing:
            # Update image for products that already exist
            existing.image = p["image"]
            existing.description = p["description"]
            existing.price = p["price"]
            existing.stock = p["stock"]
            existing.category_id = p["category"].id
        else:
            # Create new product with image
            db.session.add(
                StationeryProduct(
                    name=p["name"],
                    category_id=p["category"].id,
                    description=p["description"],
                    price=p["price"],
                    stock=p["stock"],
                    image=p["image"],
                )
            )

    db.session.commit()

    print("Stationery products and images seeded.")


def seed_coupons():
    if not Coupon.query.filter_by(code="WELCOME50").first():
        db.session.add(
            Coupon(
                code="WELCOME50",
                discount_type="PERCENT",
                discount_value=50,
                minimum_order_value=100,
                maximum_discount=50,
                active=True,
            )
        )

    if not Coupon.query.filter_by(code="FLAT20").first():
        db.session.add(
            Coupon(
                code="FLAT20",
                discount_type="FIXED",
                discount_value=20,
                minimum_order_value=150,
                active=True,
            )
        )

    db.session.commit()

    print("Coupons seeded.")


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

    if Admin.query.filter_by(username=username).first():
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
        "IMPORTANT: log in and consider changing this password, "
        "and never commit the real password to Git."
    )


def main():
    with app.app_context():

        db.create_all()

        print(
            "Tables created (if they did not already exist)."
        )

        seed_settings()

        categories = seed_categories()

        seed_printing_services(categories)

        seed_stationery(categories)

        seed_coupons()

        seed_admin()

        print("\nSeeding complete.")


if __name__ == "__main__":
    main()