"""
PrintCare Database Setup + Seed Script

Run from project root:

    python database/seed.py

This script:
1. Creates database tables if they do not exist.
2. Seeds application settings.
3. Seeds printing and stationery categories.
4. Seeds printing services.
5. Adds/updates 100 stationery products.
6. Seeds coupons.
7. Creates the initial admin account.

IMPORTANT:
The current project has only 8 stationery image files.
Therefore, multiple products temporarily use the available
images. We can add unique product images later.
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
    StationeryProduct,
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
            "PrintCare",
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
# CATEGORIES
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

    stationery_categories = [
        "Pens & Pencils",
        "Notebooks & Registers",
        "Files & Folders",
        "Office Supplies",
        "Art & Craft",
        "Geometry & Instruments",
        "Paper & Envelopes",
        "Calculators",
        "School Essentials",
        "Adhesives & Correction"
    ]

    created = {}

    # --------------------------------------------------------
    # PRINTING CATEGORIES
    # --------------------------------------------------------

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
                icon="printer"
            )

            db.session.add(category)

        created[("printing", name)] = category

    # --------------------------------------------------------
    # STATIONERY CATEGORIES
    # --------------------------------------------------------

    for index, name in enumerate(stationery_categories):

        category = Category.query.filter_by(
            name=name,
            kind="stationery"
        ).first()

        if not category:

            category = Category(
                name=name,
                kind="stationery",
                sort_order=index,
                icon="pen"
            )

            db.session.add(category)

        created[("stationery", name)] = category

    db.session.commit()

    print("Categories seeded.")

    return created


# ============================================================
# PRINTING SERVICES
# ============================================================

def seed_printing_services(categories):

    bw = categories[("printing", "B&W Print")]
    color = categories[("printing", "Color Print")]
    binding = categories[("printing", "Binding")]
    scan = categories[("printing", "Scan")]

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
                "price_per_page",
                0
            )
            existing.double_side_extra = service.get(
                "double_side_extra",
                0
            )
            existing.is_configurable = service.get(
                "is_configurable",
                True
            )
            existing.flat_price = service.get(
                "flat_price"
            )

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
                        "price_per_page",
                        0
                    ),
                    double_side_extra=service.get(
                        "double_side_extra",
                        0
                    ),
                    is_configurable=service.get(
                        "is_configurable",
                        True
                    ),
                    flat_price=service.get(
                        "flat_price"
                    )
                )
            )

    db.session.commit()

    print("Printing services seeded.")


# ============================================================
# STATIONERY PRODUCTS - 100 PRODUCTS
# ============================================================

def seed_stationery(categories):

    pens = categories[
        ("stationery", "Pens & Pencils")
    ]

    notebooks = categories[
        ("stationery", "Notebooks & Registers")
    ]

    files = categories[
        ("stationery", "Files & Folders")
    ]

    office = categories[
        ("stationery", "Office Supplies")
    ]

    art = categories[
        ("stationery", "Art & Craft")
    ]

    geometry = categories[
        ("stationery", "Geometry & Instruments")
    ]

    paper = categories[
        ("stationery", "Paper & Envelopes")
    ]

    calculators = categories[
        ("stationery", "Calculators")
    ]

    school = categories[
        ("stationery", "School Essentials")
    ]

    adhesives = categories[
        ("stationery", "Adhesives & Correction")
    ]

    # ========================================================
    # 100 PRODUCTS
    # ========================================================

    products = [

        # ====================================================
        # 1-20 : PENS & PENCILS
        # ====================================================

        {
            "name": "Cello Butterflow Ball Pen - Blue",
            "category": pens,
            "price": 10,
            "stock": 200,
            "image": "images/stationery/pen.png",
            "description": "Smooth blue ball pen for everyday writing."
        },

        {
            "name": "Cello Butterflow Ball Pen - Black",
            "category": pens,
            "price": 10,
            "stock": 200,
            "image": "images/stationery/pen.png",
            "description": "Smooth black ball pen for everyday writing."
        },

        {
            "name": "Reynolds 045 Ball Pen - Blue",
            "category": pens,
            "price": 10,
            "stock": 180,
            "image": "images/stationery/pen.png",
            "description": "Popular blue ball pen with comfortable grip."
        },

        {
            "name": "Reynolds 045 Ball Pen - Black",
            "category": pens,
            "price": 10,
            "stock": 180,
            "image": "images/stationery/pen.png",
            "description": "Reliable black ball pen for daily use."
        },

        {
            "name": "Flair Writo-meter Ball Pen",
            "category": pens,
            "price": 10,
            "stock": 150,
            "image": "images/stationery/pen.png",
            "description": "Smooth writing Flair ball pen."
        },

        {
            "name": "Flair Marathon Ball Pen",
            "category": pens,
            "price": 10,
            "stock": 150,
            "image": "images/stationery/pen.png",
            "description": "Comfortable everyday writing pen."
        },

        {
            "name": "Classmate Octane Ball Pen",
            "category": pens,
            "price": 10,
            "stock": 160,
            "image": "images/stationery/pen.png",
            "description": "Smooth-writing pen suitable for students."
        },

        {
            "name": "Pentonic Ball Pen",
            "category": pens,
            "price": 10,
            "stock": 160,
            "image": "images/stationery/pen.png",
            "description": "Modern smooth-flow ball pen."
        },

        {
            "name": "Linc Ocean Gel Pen",
            "category": pens,
            "price": 10,
            "stock": 140,
            "image": "images/stationery/pen.png",
            "description": "Smooth gel pen for comfortable writing."
        },

        {
            "name": "Linc Glycer Gel Pen",
            "category": pens,
            "price": 10,
            "stock": 140,
            "image": "images/stationery/pen.png",
            "description": "Fine gel writing pen."
        },

        {
            "name": "Pilot V7 Roller Ball Pen",
            "category": pens,
            "price": 80,
            "stock": 80,
            "image": "images/stationery/pen.png",
            "description": "Premium liquid ink roller ball pen."
        },

        {
            "name": "Pilot V5 Roller Ball Pen",
            "category": pens,
            "price": 75,
            "stock": 80,
            "image": "images/stationery/pen.png",
            "description": "Fine-point roller ball pen."
        },

        {
            "name": "Luxor Pilot Pen",
            "category": pens,
            "price": 30,
            "stock": 100,
            "image": "images/stationery/pen.png",
            "description": "Reliable smooth-writing pen."
        },

        {
            "name": "Parker Jotter Ball Pen",
            "category": pens,
            "price": 350,
            "stock": 30,
            "image": "images/stationery/pen.png",
            "description": "Premium Parker ball pen for professional use."
        },

        {
            "name": "Apsara Platinum Pencil - Pack of 10",
            "category": pens,
            "price": 60,
            "stock": 120,
            "image": "images/stationery/pencil.png",
            "description": "HB graphite pencils for writing and drawing."
        },

        {
            "name": "Nataraj HB Pencil - Pack of 10",
            "category": pens,
            "price": 45,
            "stock": 150,
            "image": "images/stationery/pencil.png",
            "description": "Classic HB pencils for school and college."
        },

        {
            "name": "DOMS Groove Pencil - Pack of 10",
            "category": pens,
            "price": 55,
            "stock": 120,
            "image": "images/stationery/pencil.png",
            "description": "Comfortable grip pencils for students."
        },

        {
            "name": "Faber-Castell Pencil - Pack of 10",
            "category": pens,
            "price": 70,
            "stock": 100,
            "image": "images/stationery/pencil.png",
            "description": "Quality graphite pencils."
        },

        {
            "name": "Camlin Supreme Pencil - Pack of 10",
            "category": pens,
            "price": 55,
            "stock": 100,
            "image": "images/stationery/pencil.png",
            "description": "Smooth graphite pencils for everyday use."
        },

        {
            "name": "Mechanical Pencil 0.5mm",
            "category": pens,
            "price": 35,
            "stock": 100,
            "image": "images/stationery/pencil.png",
            "description": "Reusable 0.5mm mechanical pencil."
        },

        # ====================================================
        # 21-40 : NOTEBOOKS & REGISTERS
        # ====================================================

        {
            "name": "Classmate A4 Notebook - 200 Pages",
            "category": notebooks,
            "price": 90,
            "stock": 100,
            "image": "images/stationery/nootbook.png",
            "description": "A4 ruled notebook for college and school."
        },

        {
            "name": "Classmate Long Notebook - 172 Pages",
            "category": notebooks,
            "price": 70,
            "stock": 100,
            "image": "images/stationery/nootbook.png",
            "description": "Ruled notebook for daily study."
        },

        {
            "name": "Classmate Pulse Notebook",
            "category": notebooks,
            "price": 80,
            "stock": 90,
            "image": "images/stationery/nootbook.png",
            "description": "Stylish notebook for students."
        },

        {
            "name": "Navneet Youva Notebook - 200 Pages",
            "category": notebooks,
            "price": 75,
            "stock": 100,
            "image": "images/stationery/nootbook.png",
            "description": "Ruled notebook for notes and assignments."
        },

        {
            "name": "Navneet Youva Long Book",
            "category": notebooks,
            "price": 65,
            "stock": 100,
            "image": "images/stationery/nootbook.png",
            "description": "Long ruled notebook for everyday writing."
        },

        {
            "name": "Camlin Notebook - 200 Pages",
            "category": notebooks,
            "price": 80,
            "stock": 100,
            "image": "images/stationery/nootbook.png",
            "description": "Quality ruled notebook."
        },

        {
            "name": "Paperkraft Premium Notebook",
            "category": notebooks,
            "price": 180,
            "stock": 60,
            "image": "images/stationery/nootbook.png",
            "description": "Premium notebook for professional notes."
        },

        {
            "name": "Spiral Notebook - Pocket Size",
            "category": notebooks,
            "price": 55,
            "stock": 120,
            "image": "images/stationery/spiral_nootbook.png",
            "description": "Compact spiral notebook."
        },

        {
            "name": "A4 Spiral Notebook - 200 Pages",
            "category": notebooks,
            "price": 120,
            "stock": 90,
            "image": "images/stationery/spiral_nootbook.png",
            "description": "Large spiral notebook for projects."
        },

        {
            "name": "A5 Spiral Notebook",
            "category": notebooks,
            "price": 80,
            "stock": 100,
            "image": "images/stationery/spiral_nootbook.png",
            "description": "Portable A5 spiral notebook."
        },

        {
            "name": "College Register - 300 Pages",
            "category": notebooks,
            "price": 140,
            "stock": 80,
            "image": "images/stationery/nootbook.png",
            "description": "Large register for college notes."
        },

        {
            "name": "Practical Record Book",
            "category": notebooks,
            "price": 100,
            "stock": 100,
            "image": "images/stationery/nootbook.png",
            "description": "Record book for practical subjects."
        },

        {
            "name": "Project Notebook",
            "category": notebooks,
            "price": 110,
            "stock": 80,
            "image": "images/stationery/nootbook.png",
            "description": "Notebook suitable for project documentation."
        },

        {
            "name": "Drawing Notebook",
            "category": notebooks,
            "price": 90,
            "stock": 80,
            "image": "images/stationery/nootbook.png",
            "description": "Plain pages for drawing and diagrams."
        },

        {
            "name": "Mini Memo Notebook",
            "category": notebooks,
            "price": 40,
            "stock": 150,
            "image": "images/stationery/spiral_nootbook.png",
            "description": "Small notebook for quick notes."
        },

        {
            "name": "Hardbound Notebook",
            "category": notebooks,
            "price": 160,
            "stock": 60,
            "image": "images/stationery/nootbook.png",
            "description": "Durable hardbound notebook."
        },

        {
            "name": "A4 Plain Notebook",
            "category": notebooks,
            "price": 75,
            "stock": 100,
            "image": "images/stationery/nootbook.png",
            "description": "Plain A4 notebook for projects and sketches."
        },

        {
            "name": "Assignment Notebook",
            "category": notebooks,
            "price": 65,
            "stock": 120,
            "image": "images/stationery/nootbook.png",
            "description": "Notebook designed for assignments."
        },

        {
            "name": "Meeting Notebook",
            "category": notebooks,
            "price": 100,
            "stock": 70,
            "image": "images/stationery/nootbook.png",
            "description": "Professional notebook for meetings."
        },

        {
            "name": "Daily Planner Notebook",
            "category": notebooks,
            "price": 150,
            "stock": 60,
            "image": "images/stationery/spiral_nootbook.png",
            "description": "Planner notebook for organizing daily tasks."
        },

        # ====================================================
        # 41-52 : FILES & FOLDERS
        # ====================================================

        {
            "name": "Plastic File Folder - Pack of 5",
            "category": files,
            "price": 120,
            "stock": 80,
            "image": "images/stationery/file_foolder.png",
            "description": "Durable plastic file folders."
        },

        {
            "name": "Solo Document File",
            "category": files,
            "price": 50,
            "stock": 100,
            "image": "images/stationery/file_foolder.png",
            "description": "Simple document storage file."
        },

        {
            "name": "Solo Expanding File",
            "category": files,
            "price": 220,
            "stock": 50,
            "image": "images/stationery/file_foolder.png",
            "description": "Expanding file for organizing documents."
        },

        {
            "name": "Ring Binder File",
            "category": files,
            "price": 150,
            "stock": 60,
            "image": "images/stationery/binder.png",
            "description": "2-ring binder for documents."
        },

        {
            "name": "A4 Lever Arch File",
            "category": files,
            "price": 180,
            "stock": 60,
            "image": "images/stationery/binder.png",
            "description": "Strong file for document storage."
        },

        {
            "name": "College Assignment File",
            "category": files,
            "price": 65,
            "stock": 100,
            "image": "images/stationery/file_foolder.png",
            "description": "File for assignments and project work."
        },

        {
            "name": "Transparent File - Pack of 10",
            "category": files,
            "price": 130,
            "stock": 80,
            "image": "images/stationery/file_foolder.png",
            "description": "Transparent document sleeves."
        },

        {
            "name": "Button File Folder",
            "category": files,
            "price": 35,
            "stock": 150,
            "image": "images/stationery/file_foolder.png",
            "description": "Button closure folder for documents."
        },

        {
            "name": "Display File - 20 Pockets",
            "category": files,
            "price": 100,
            "stock": 80,
            "image": "images/stationery/file_foolder.png",
            "description": "Display file with multiple pockets."
        },

        {
            "name": "Document Folder - Pack of 3",
            "category": files,
            "price": 90,
            "stock": 100,
            "image": "images/stationery/file_foolder.png",
            "description": "Set of folders for document organization."
        },

        {
            "name": "Project File Folder",
            "category": files,
            "price": 60,
            "stock": 120,
            "image": "images/stationery/file_foolder.png",
            "description": "Useful folder for college projects."
        },

        {
            "name": "Certificate File",
            "category": files,
            "price": 100,
            "stock": 70,
            "image": "images/stationery/binder.png",
            "description": "Protective file for certificates."
        },

        # ====================================================
        # 53-62 : OFFICE SUPPLIES
        # ====================================================

        {
            "name": "Stapler with Pins",
            "category": office,
            "price": 99,
            "stock": 70,
            "image": "images/stationery/stapler.png",
            "description": "Compact stapler with pins."
        },

        {
            "name": "Kangaro Stapler",
            "category": office,
            "price": 120,
            "stock": 60,
            "image": "images/stationery/stapler.png",
            "description": "Reliable desktop stapler."
        },

        {
            "name": "Staple Pins No.10",
            "category": office,
            "price": 20,
            "stock": 150,
            "image": "images/stationery/stapler.png",
            "description": "Standard staple pins."
        },

        {
            "name": "Sticky Notes - Pack of 4",
            "category": office,
            "price": 70,
            "stock": 140,
            "image": "images/stationery/sticky_notes.png",
            "description": "Assorted colour sticky notes."
        },

        {
            "name": "Sticky Notes - Neon",
            "category": office,
            "price": 50,
            "stock": 130,
            "image": "images/stationery/sticky_notes.png",
            "description": "Bright neon sticky notes."
        },

        {
            "name": "Paper Clips - Pack of 100",
            "category": office,
            "price": 30,
            "stock": 150,
            "image": "images/stationery/sticky_notes.png",
            "description": "Metal paper clips for organizing papers."
        },

        {
            "name": "Binder Clips - Pack of 12",
            "category": office,
            "price": 60,
            "stock": 100,
            "image": "images/stationery/stapler.png",
            "description": "Strong binder clips for documents."
        },

        {
            "name": "Whiteboard Marker - Pack of 4",
            "category": office,
            "price": 80,
            "stock": 100,
            "image": "images/stationery/pen.png",
            "description": "Dry erase markers for whiteboards."
        },

        {
            "name": "Permanent Marker - Black",
            "category": office,
            "price": 30,
            "stock": 120,
            "image": "images/stationery/pen.png",
            "description": "Permanent black marker."
        },

        {
            "name": "Desk Organizer",
            "category": office,
            "price": 180,
            "stock": 50,
            "image": "images/stationery/binder.png",
            "description": "Desk organizer for stationery items."
        },

        # ====================================================
        # 63-70 : ART & CRAFT
        # ====================================================

        {
            "name": "DOMS Colour Pencils - 12 Shades",
            "category": art,
            "price": 75,
            "stock": 100,
            "image": "images/stationery/pencil.png",
            "description": "Colour pencil set with 12 shades."
        },

        {
            "name": "DOMS Colour Pencils - 24 Shades",
            "category": art,
            "price": 150,
            "stock": 70,
            "image": "images/stationery/pencil.png",
            "description": "Colour pencil set with 24 shades."
        },

        {
            "name": "Faber-Castell Colour Pencils - 12",
            "category": art,
            "price": 100,
            "stock": 80,
            "image": "images/stationery/pencil.png",
            "description": "Quality colour pencils."
        },

        {
            "name": "Camlin Sketch Pens - 12 Colours",
            "category": art,
            "price": 70,
            "stock": 90,
            "image": "images/stationery/pen.png",
            "description": "Bright sketch pens for drawing."
        },

        {
            "name": "Camlin Sketch Pens - 24 Colours",
            "category": art,
            "price": 130,
            "stock": 70,
            "image": "images/stationery/pen.png",
            "description": "Large sketch pen set."
        },

        {
            "name": "Wax Crayons - 12 Colours",
            "category": art,
            "price": 50,
            "stock": 100,
            "image": "images/stationery/pencil.png",
            "description": "Colourful wax crayons."
        },

        {
            "name": "Oil Pastels - 12 Shades",
            "category": art,
            "price": 80,
            "stock": 80,
            "image": "images/stationery/pencil.png",
            "description": "Smooth oil pastel set."
        },

        {
            "name": "Drawing Pencil Set",
            "category": art,
            "price": 120,
            "stock": 60,
            "image": "images/stationery/pencil.png",
            "description": "Drawing pencils for sketches."
        },

        # ====================================================
        # 71-78 : GEOMETRY & INSTRUMENTS
        # ====================================================

        {
            "name": "Camlin Geometry Box",
            "category": geometry,
            "price": 120,
            "stock": 80,
            "image": "images/stationery/pencil.png",
            "description": "Complete geometry instrument box."
        },

        {
            "name": "DOMS Geometry Box",
            "category": geometry,
            "price": 100,
            "stock": 80,
            "image": "images/stationery/pencil.png",
            "description": "Student geometry set."
        },

        {
            "name": "30cm Plastic Ruler",
            "category": geometry,
            "price": 20,
            "stock": 150,
            "image": "images/stationery/pencil.png",
            "description": "30cm transparent ruler."
        },

        {
            "name": "15cm Ruler",
            "category": geometry,
            "price": 10,
            "stock": 180,
            "image": "images/stationery/pencil.png",
            "description": "Compact ruler for school use."
        },

        {
            "name": "Compass Set",
            "category": geometry,
            "price": 60,
            "stock": 100,
            "image": "images/stationery/pencil.png",
            "description": "Compass and geometry tools."
        },

        {
            "name": "Protractor 180 Degree",
            "category": geometry,
            "price": 15,
            "stock": 150,
            "image": "images/stationery/pencil.png",
            "description": "Transparent 180-degree protractor."
        },

        {
            "name": "Set Square Pair",
            "category": geometry,
            "price": 40,
            "stock": 100,
            "image": "images/stationery/pencil.png",
            "description": "Pair of geometry set squares."
        },

        {
            "name": "Metal Scale 30cm",
            "category": geometry,
            "price": 50,
            "stock": 80,
            "image": "images/stationery/pencil.png",
            "description": "Durable metal ruler."
        },

        # ====================================================
        # 79-84 : PAPER & ENVELOPES
        # ====================================================

        {
            "name": "A4 Copier Paper - 100 Sheets",
            "category": paper,
            "price": 70,
            "stock": 100,
            "image": "images/stationery/nootbook.png",
            "description": "White A4 paper for printing and photocopying."
        },

        {
            "name": "A4 Copier Paper - 500 Sheets",
            "category": paper,
            "price": 320,
            "stock": 50,
            "image": "images/stationery/nootbook.png",
            "description": "A4 copier paper ream."
        },

        {
            "name": "A3 Paper - 100 Sheets",
            "category": paper,
            "price": 180,
            "stock": 50,
            "image": "images/stationery/nootbook.png",
            "description": "A3 sheets for printing and projects."
        },

        {
            "name": "A4 Colour Paper - 100 Sheets",
            "category": paper,
            "price": 120,
            "stock": 70,
            "image": "images/stationery/nootbook.png",
            "description": "Assorted colour A4 paper."
        },

        {
            "name": "White Envelope - Pack of 25",
            "category": paper,
            "price": 60,
            "stock": 100,
            "image": "images/stationery/file_foolder.png",
            "description": "White envelopes for documents and letters."
        },

        {
            "name": "Document Envelope - Pack of 10",
            "category": paper,
            "price": 80,
            "stock": 100,
            "image": "images/stationery/file_foolder.png",
            "description": "Large envelopes for documents."
        },

        # ====================================================
        # 85-90 : CALCULATORS
        # ====================================================

        {
            "name": "Casio MJ-120D Calculator",
            "category": calculators,
            "price": 550,
            "stock": 40,
            "image": "images/stationery/pen.png",
            "description": "Basic desktop calculator for everyday calculations."
        },

        {
            "name": "Casio MS-8B Calculator",
            "category": calculators,
            "price": 450,
            "stock": 40,
            "image": "images/stationery/pen.png",
            "description": "Compact basic calculator."
        },

        {
            "name": "Casio FX-82MS Scientific Calculator",
            "category": calculators,
            "price": 650,
            "stock": 50,
            "image": "images/stationery/pen.png",
            "description": "Scientific calculator for students."
        },

        {
            "name": "Casio FX-991ES Plus",
            "category": calculators,
            "price": 1200,
            "stock": 30,
            "image": "images/stationery/pen.png",
            "description": "Advanced scientific calculator."
        },

        {
            "name": "Citizen Basic Calculator",
            "category": calculators,
            "price": 300,
            "stock": 50,
            "image": "images/stationery/pen.png",
            "description": "Affordable desktop calculator."
        },

        {
            "name": "Orpat Basic Calculator",
            "category": calculators,
            "price": 250,
            "stock": 50,
            "image": "images/stationery/pen.png",
            "description": "Simple calculator for everyday use."
        },

        # ====================================================
        # 91-95 : SCHOOL ESSENTIALS
        # ====================================================

        {
            "name": "Nataraj Eraser - Pack of 5",
            "category": school,
            "price": 20,
            "stock": 150,
            "image": "images/stationery/pencil.png",
            "description": "Soft erasers for pencil writing."
        },

        {
            "name": "Apsara Eraser - Pack of 5",
            "category": school,
            "price": 25,
            "stock": 150,
            "image": "images/stationery/pencil.png",
            "description": "Clean-writing erasers."
        },

        {
            "name": "DOMS Sharpener - Pack of 5",
            "category": school,
            "price": 30,
            "stock": 150,
            "image": "images/stationery/pencil.png",
            "description": "Compact pencil sharpeners."
        },

        {
            "name": "Pencil Box",
            "category": school,
            "price": 100,
            "stock": 80,
            "image": "images/stationery/binder.png",
            "description": "Storage box for pens and pencils."
        },

        {
            "name": "College ID Card Holder",
            "category": school,
            "price": 40,
            "stock": 100,
            "image": "images/stationery/file_foolder.png",
            "description": "Simple ID card holder."
        },

        # ====================================================
        # 96-100 : ADHESIVES & CORRECTION
        # ====================================================

        {
            "name": "Fevicol MR - 50g",
            "category": adhesives,
            "price": 35,
            "stock": 100,
            "image": "images/stationery/sticky_notes.png",
            "description": "White adhesive for paper and craft work."
        },

        {
            "name": "Fevistik Glue Stick - 15g",
            "category": adhesives,
            "price": 40,
            "stock": 100,
            "image": "images/stationery/sticky_notes.png",
            "description": "Easy-to-use glue stick."
        },

        {
            "name": "Camlin Correction Pen",
            "category": adhesives,
            "price": 35,
            "stock": 100,
            "image": "images/stationery/pen.png",
            "description": "Correction pen for clean document editing."
        },

        {
            "name": "Correction Tape",
            "category": adhesives,
            "price": 45,
            "stock": 100,
            "image": "images/stationery/pen.png",
            "description": "Quick-dry correction tape."
        },

        {
            "name": "Double Side Tape",
            "category": adhesives,
            "price": 50,
            "stock": 80,
            "image": "images/stationery/sticky_notes.png",
            "description": "Double-sided adhesive tape for craft and office use."
        }
    ]

    # ========================================================
    # ADD / UPDATE PRODUCTS
    # ========================================================

    for product in products:

        existing = StationeryProduct.query.filter_by(
            name=product["name"]
        ).first()

        if existing:

            existing.category_id = product["category"].id
            existing.description = product["description"]
            existing.price = product["price"]
            existing.stock = product["stock"]
            existing.image = product["image"]
            existing.is_active = True

        else:

            db.session.add(
                StationeryProduct(
                    name=product["name"],
                    category_id=product["category"].id,
                    description=product["description"],
                    price=product["price"],
                    stock=product["stock"],
                    image=product["image"],
                    is_active=True
                )
            )

    db.session.commit()

    print(
        f"Stationery products seeded/updated: {len(products)}"
    )


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

        seed_stationery(categories)

        seed_coupons()

        seed_admin()

        print()
        print("==========================================")
        print("       PRINTCARE SEEDING COMPLETE")
        print("==========================================")
        print("100 stationery products added/updated.")
        print("==========================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()