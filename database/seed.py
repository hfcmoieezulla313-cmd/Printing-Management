"""
Printify Database Setup + Seed Script

Run from project root:

    python database/seed.py

This script:
1. Creates database tables if they do not exist.
2. Seeds application settings.
3. Seeds printing and stationery categories.
4. Seeds printing services.
5. Deactivates the old stationery catalog.
6. Adds/updates the new Printify stationery catalog.
7. Seeds coupons.
8. Creates the initial admin account.

NOTE:
The new stationery products use image paths under
static/images/stationery/. Add the matching PNG files
to that folder so the product cards show the product images.
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

    # New Printify stationery catalog categories.
    stationery_categories = [
        "Notebooks & Journals",
        "Pens & Writing",
        "Highlighters",
        "Sticky Notes",
        "Art Supplies",
        "Office Supplies",
        "Bags & Pouches",
        "Water Bottles",
        "Tech Accessories",
        "Lunch Boxes",
        "Keychains & Accessories"
    ]

    category_icons = {
        "Notebooks & Journals": "notebook",
        "Pens & Writing": "pen",
        "Highlighters": "highlighter",
        "Sticky Notes": "sticky-note",
        "Art Supplies": "palette",
        "Office Supplies": "briefcase",
        "Bags & Pouches": "bag",
        "Water Bottles": "bottle",
        "Tech Accessories": "laptop",
        "Lunch Boxes": "lunch-box",
        "Keychains & Accessories": "keychain"
    }

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
                icon="printer",
                is_active=True
            )

            db.session.add(category)

        else:
            category.sort_order = index
            category.icon = "printer"
            category.is_active = True

        created[("printing", name)] = category

    # --------------------------------------------------------
    # DEACTIVATE OLD STATIONERY CATEGORIES
    # --------------------------------------------------------

    for category in Category.query.filter_by(kind="stationery").all():
        category.is_active = False

    # --------------------------------------------------------
    # CREATE / UPDATE NEW STATIONERY CATEGORIES
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
                icon=category_icons.get(name, "box"),
                is_active=True
            )

            db.session.add(category)

        else:
            category.sort_order = index
            category.icon = category_icons.get(name, "box")
            category.is_active = True

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
# STATIONERY PRODUCTS - 70 PRODUCTS
# ============================================================

def seed_stationery(categories):

    # --------------------------------------------------------
    # NEW PRINTIFY STATIONERY CATALOG
    # --------------------------------------------------------

    notebooks = categories[("stationery", "Notebooks & Journals")]
    writing = categories[("stationery", "Pens & Writing")]
    highlighters = categories[("stationery", "Highlighters")]
    sticky_notes = categories[("stationery", "Sticky Notes")]
    art = categories[("stationery", "Art Supplies")]
    office = categories[("stationery", "Office Supplies")]
    bags = categories[("stationery", "Bags & Pouches")]
    bottles = categories[("stationery", "Water Bottles")]
    tech = categories[("stationery", "Tech Accessories")]
    lunch = categories[("stationery", "Lunch Boxes")]
    accessories = categories[("stationery", "Keychains & Accessories")]

    # Keep old products in the database for historical orders/cart references,
    # but hide them from the active stationery catalog.
    for existing_product in StationeryProduct.query.all():
        existing_product.is_active = False

    products = [
        # ====================================================
        # NOTEBOOKS & JOURNALS (8)
        # ====================================================
        {
            "name": "A5 Minimal Hardcover Journal",
            "category": notebooks,
            "price": 149,
            "stock": 80,
            "image": "images/stationery/a5-hardcover-journal.png",
            "description": "Clean hardcover journal with smooth pages for notes, ideas and planning."
        },
        {
            "name": "A5 Dotted Notebook",
            "category": notebooks,
            "price": 179,
            "stock": 75,
            "image": "images/stationery/a5-dotted-notebook.png",
            "description": "Premium dotted notebook for study notes, journaling and creative layouts."
        },
        {
            "name": "A4 Ruled Study Notebook",
            "category": notebooks,
            "price": 119,
            "stock": 90,
            "image": "images/stationery/a4-ruled-notebook.png",
            "description": "Spacious ruled notebook for lectures, assignments and daily study."
        },
        {
            "name": "A5 Spiral Study Notebook",
            "category": notebooks,
            "price": 99,
            "stock": 100,
            "image": "images/stationery/a5-spiral-notebook.png",
            "description": "Compact spiral notebook with easy-turn pages for everyday notes."
        },
        {
            "name": "Hardcover Daily Planner",
            "category": notebooks,
            "price": 229,
            "stock": 60,
            "image": "images/stationery/daily-planner.png",
            "description": "Daily planner with sections for tasks, priorities and schedules."
        },
        {
            "name": "Project Record Notebook",
            "category": notebooks,
            "price": 139,
            "stock": 70,
            "image": "images/stationery/project-record-notebook.png",
            "description": "Practical notebook for project records, observations and documentation."
        },
        {
            "name": "Pocket Memo Notebook",
            "category": notebooks,
            "price": 69,
            "stock": 120,
            "image": "images/stationery/pocket-memo-notebook.png",
            "description": "Small portable notebook for quick reminders and short notes."
        },
        {
            "name": "Premium Black Notebook",
            "category": notebooks,
            "price": 199,
            "stock": 65,
            "image": "images/stationery/premium-black-notebook.png",
            "description": "Simple premium notebook with a durable cover and clean ruled pages."
        },

        # ====================================================
        # PENS & WRITING (8)
        # ====================================================
        {
            "name": "SmoothFlow Gel Pen Set - 5",
            "category": writing,
            "price": 129,
            "stock": 120,
            "image": "images/stationery/gel-pen-set.png",
            "description": "Set of five smooth gel pens for everyday writing and study work."
        },
        {
            "name": "Executive Metal Ball Pen",
            "category": writing,
            "price": 79,
            "stock": 90,
            "image": "images/stationery/executive-ball-pen.png",
            "description": "Sleek metal-finish ball pen designed for comfortable everyday writing."
        },
        {
            "name": "Fine Tip Blue Pen Set - 10",
            "category": writing,
            "price": 109,
            "stock": 120,
            "image": "images/stationery/fine-tip-blue-pens.png",
            "description": "Ten fine-tip blue pens for neat handwriting and note taking."
        },
        {
            "name": "Black Ink Ball Pen Set - 10",
            "category": writing,
            "price": 109,
            "stock": 120,
            "image": "images/stationery/black-ball-pens.png",
            "description": "Smooth black ink pens suitable for forms, notes and office work."
        },
        {
            "name": "QuickDry Roller Pen - Blue",
            "category": writing,
            "price": 49,
            "stock": 100,
            "image": "images/stationery/blue-roller-pen.png",
            "description": "Fine roller pen with smooth blue ink and comfortable grip."
        },
        {
            "name": "QuickDry Roller Pen - Black",
            "category": writing,
            "price": 49,
            "stock": 100,
            "image": "images/stationery/black-roller-pen.png",
            "description": "Fine roller pen with smooth black ink for clean writing."
        },
        {
            "name": "0.5mm Mechanical Pencil Set - 3",
            "category": writing,
            "price": 99,
            "stock": 90,
            "image": "images/stationery/mechanical-pencils.png",
            "description": "Three reusable 0.5mm mechanical pencils for writing and drawing."
        },
        {
            "name": "HB Pencil Pack - 10",
            "category": writing,
            "price": 59,
            "stock": 150,
            "image": "images/stationery/hb-pencils.png",
            "description": "HB graphite pencils for school work, sketching and everyday writing."
        },

        # ====================================================
        # HIGHLIGHTERS (6)
        # ====================================================
        {
            "name": "Pastel Highlighter Set - 6",
            "category": highlighters,
            "price": 149,
            "stock": 85,
            "image": "images/stationery/pastel-highlighters.png",
            "description": "Six soft pastel highlighters for notes, textbooks and planners."
        },
        {
            "name": "Dual Tip Highlighter Set - 4",
            "category": highlighters,
            "price": 199,
            "stock": 70,
            "image": "images/stationery/dual-tip-highlighters.png",
            "description": "Four dual-tip highlighters with flexible tips for highlighting and underlining."
        },
        {
            "name": "Neon Highlighter Set - 5",
            "category": highlighters,
            "price": 119,
            "stock": 90,
            "image": "images/stationery/neon-highlighters.png",
            "description": "Bright neon shades that make important notes easy to spot."
        },
        {
            "name": "Mini Highlighter Set - 6",
            "category": highlighters,
            "price": 99,
            "stock": 110,
            "image": "images/stationery/mini-highlighters.png",
            "description": "Compact highlighters that fit easily into pencil cases and pouches."
        },
        {
            "name": "Desk Highlighter Trio",
            "category": highlighters,
            "price": 79,
            "stock": 100,
            "image": "images/stationery/highlighter-trio.png",
            "description": "Three everyday highlighter colours for study and office notes."
        },
        {
            "name": "Soft Tone Highlighter Set - 8",
            "category": highlighters,
            "price": 219,
            "stock": 65,
            "image": "images/stationery/soft-tone-highlighters.png",
            "description": "Eight muted highlighter shades for organized and comfortable reading."
        },

        # ====================================================
        # STICKY NOTES (5)
        # ====================================================
        {
            "name": "Pastel Sticky Notes - 4 Pack",
            "category": sticky_notes,
            "price": 99,
            "stock": 140,
            "image": "images/stationery/pastel-sticky-notes.png",
            "description": "Four pastel sticky-note pads for reminders, study notes and quick lists."
        },
        {
            "name": "Index Page Flags - 8 Colour",
            "category": sticky_notes,
            "price": 79,
            "stock": 100,
            "image": "images/stationery/page-flags.png",
            "description": "Eight colour page flags for organizing books, documents and assignments."
        },
        {
            "name": "Square Memo Notes - 3 Pack",
            "category": sticky_notes,
            "price": 89,
            "stock": 110,
            "image": "images/stationery/square-memo-notes.png",
            "description": "Three memo pads for reminders, to-do lists and desk notes."
        },
        {
            "name": "Arrow Sticky Flags - 6 Colour",
            "category": sticky_notes,
            "price": 69,
            "stock": 125,
            "image": "images/stationery/arrow-sticky-flags.png",
            "description": "Arrow-shaped flags for marking important lines and pages."
        },
        {
            "name": "Large Sticky Note Pad",
            "category": sticky_notes,
            "price": 79,
            "stock": 100,
            "image": "images/stationery/large-sticky-notes.png",
            "description": "Large writable sticky notes for detailed reminders and planning."
        },

        # ====================================================
        # ART SUPPLIES (8)
        # ====================================================
        {
            "name": "Colour Marker Set - 24",
            "category": art,
            "price": 299,
            "stock": 60,
            "image": "images/stationery/colour-marker-set.png",
            "description": "Twenty-four vibrant markers for drawing, lettering and creative projects."
        },
        {
            "name": "Sketching Pencil Set - 12",
            "category": art,
            "price": 199,
            "stock": 65,
            "image": "images/stationery/sketching-pencil-set.png",
            "description": "Twelve sketching pencils with a useful range of grades for shading and drawing."
        },
        {
            "name": "Colour Pencil Set - 24 Shades",
            "category": art,
            "price": 179,
            "stock": 75,
            "image": "images/stationery/colour-pencils-24.png",
            "description": "Twenty-four bright colour pencils for school art and creative work."
        },
        {
            "name": "Watercolour Paint Set - 12",
            "category": art,
            "price": 229,
            "stock": 55,
            "image": "images/stationery/watercolour-set.png",
            "description": "Twelve watercolour shades for painting, projects and creative practice."
        },
        {
            "name": "Acrylic Paint Set - 12",
            "category": art,
            "price": 249,
            "stock": 50,
            "image": "images/stationery/acrylic-paints.png",
            "description": "Twelve acrylic colours suitable for craft and canvas projects."
        },
        {
            "name": "Oil Pastel Set - 24",
            "category": art,
            "price": 189,
            "stock": 60,
            "image": "images/stationery/oil-pastels-24.png",
            "description": "Twenty-four creamy oil pastel shades for expressive artwork and blending."
        },
        {
            "name": "Fineliner Drawing Pens - 8",
            "category": art,
            "price": 149,
            "stock": 80,
            "image": "images/stationery/fineliner-pens.png",
            "description": "Eight fine drawing pens for outlines, diagrams and lettering."
        },
        {
            "name": "Paint Brush Set - 10",
            "category": art,
            "price": 129,
            "stock": 75,
            "image": "images/stationery/paint-brush-set.png",
            "description": "Mixed-size brushes for watercolour, acrylic and craft painting."
        },

        # ====================================================
        # OFFICE SUPPLIES (7)
        # ====================================================
        {
            "name": "Modern Desk Organizer",
            "category": office,
            "price": 249,
            "stock": 45,
            "image": "images/stationery/desk-organizer.png",
            "description": "Compact desk organizer with practical sections for everyday stationery."
        },
        {
            "name": "Heavy Duty Desktop Stapler",
            "category": office,
            "price": 159,
            "stock": 55,
            "image": "images/stationery/desktop-stapler.png",
            "description": "Sturdy desktop stapler for school, office and project documents."
        },
        {
            "name": "Metal Binder Clips - 12 Pack",
            "category": office,
            "price": 69,
            "stock": 100,
            "image": "images/stationery/binder-clips.png",
            "description": "Strong metal binder clips for organizing papers and documents."
        },
        {
            "name": "Paper Clip Box - 100",
            "category": office,
            "price": 49,
            "stock": 120,
            "image": "images/stationery/paper-clips.png",
            "description": "Box of paper clips for everyday office and study use."
        },
        {
            "name": "Desktop Tape Dispenser",
            "category": office,
            "price": 119,
            "stock": 65,
            "image": "images/stationery/tape-dispenser.png",
            "description": "Stable desktop tape dispenser for quick and clean cutting."
        },
        {
            "name": "Whiteboard Marker Set - 4",
            "category": office,
            "price": 89,
            "stock": 100,
            "image": "images/stationery/whiteboard-markers.png",
            "description": "Four low-odour markers for whiteboards, study rooms and meetings."
        },
        {
            "name": "Document Tray - 3 Tier",
            "category": office,
            "price": 299,
            "stock": 40,
            "image": "images/stationery/document-tray.png",
            "description": "Three-tier tray for sorting documents, files and daily paperwork."
        },

        # ====================================================
        # BAGS & POUCHES (6)
        # ====================================================
        {
            "name": "Canvas Utility Pouch",
            "category": bags,
            "price": 299,
            "stock": 50,
            "image": "images/stationery/canvas-pouch.png",
            "description": "Durable canvas pouch for pens, cables, small accessories and daily essentials."
        },
        {
            "name": "Laptop Document Sleeve",
            "category": bags,
            "price": 399,
            "stock": 35,
            "image": "images/stationery/document-sleeve.png",
            "description": "Minimal padded sleeve for carrying notebooks, documents and a compact laptop."
        },
        {
            "name": "Double Zip Pencil Pouch",
            "category": bags,
            "price": 179,
            "stock": 70,
            "image": "images/stationery/double-zip-pouch.png",
            "description": "Double-zip pouch with separate sections for pens, pencils and accessories."
        },
        {
            "name": "Slim Stationery Pouch",
            "category": bags,
            "price": 149,
            "stock": 85,
            "image": "images/stationery/slim-stationery-pouch.png",
            "description": "Slim lightweight pouch for carrying essential stationery every day."
        },
        {
            "name": "Everyday College Tote Bag",
            "category": bags,
            "price": 349,
            "stock": 45,
            "image": "images/stationery/college-tote-bag.png",
            "description": "Reusable tote bag for notebooks, files, bottles and everyday college items."
        },
        {
            "name": "Mini Travel Organizer Pouch",
            "category": bags,
            "price": 229,
            "stock": 60,
            "image": "images/stationery/travel-organizer-pouch.png",
            "description": "Compact organizer pouch for chargers, cables, pens and small essentials."
        },

        # ====================================================
        # WATER BOTTLES (5)
        # ====================================================
        {
            "name": "750ml Insulated Bottle",
            "category": bottles,
            "price": 699,
            "stock": 40,
            "image": "images/stationery/insulated-bottle.png",
            "description": "Insulated reusable bottle designed for study days, work and travel."
        },
        {
            "name": "750ml Tritan Water Bottle",
            "category": bottles,
            "price": 349,
            "stock": 65,
            "image": "images/stationery/tritan-bottle.png",
            "description": "Lightweight reusable bottle with a practical 750ml capacity."
        },
        {
            "name": "1L Sports Water Bottle",
            "category": bottles,
            "price": 399,
            "stock": 55,
            "image": "images/stationery/1l-sports-bottle.png",
            "description": "Large reusable bottle with a carry-friendly design for active days."
        },
        {
            "name": "500ml Compact Steel Bottle",
            "category": bottles,
            "price": 449,
            "stock": 50,
            "image": "images/stationery/compact-steel-bottle.png",
            "description": "Compact steel bottle sized for desks, backpacks and short trips."
        },
        {
            "name": "650ml Flip Lid Bottle",
            "category": bottles,
            "price": 299,
            "stock": 70,
            "image": "images/stationery/flip-lid-bottle.png",
            "description": "Reusable 650ml bottle with an easy flip lid for daily use."
        },

        # ====================================================
        # TECH ACCESSORIES (6)
        # ====================================================
        {
            "name": "Cable Organizer Set",
            "category": tech,
            "price": 199,
            "stock": 70,
            "image": "images/stationery/cable-organizer.png",
            "description": "Cable clips and organizers for keeping charging and desk cables tidy."
        },
        {
            "name": "32GB USB Flash Drive",
            "category": tech,
            "price": 499,
            "stock": 45,
            "image": "images/stationery/usb-drive.png",
            "description": "Compact 32GB USB drive for storing projects, documents and study files."
        },
        {
            "name": "Phone Stand - Foldable",
            "category": tech,
            "price": 149,
            "stock": 80,
            "image": "images/stationery/foldable-phone-stand.png",
            "description": "Foldable desktop phone stand for calls, videos and study sessions."
        },
        {
            "name": "6-in-1 Cable Adapter Kit",
            "category": tech,
            "price": 249,
            "stock": 55,
            "image": "images/stationery/cable-adapter-kit.png",
            "description": "Compact adapter kit for organizing and connecting common charging cables."
        },
        {
            "name": "USB Desk Light",
            "category": tech,
            "price": 329,
            "stock": 40,
            "image": "images/stationery/usb-desk-light.png",
            "description": "Compact USB-powered desk light for focused study and work."
        },
        {
            "name": "Wireless Mouse Pad - Basic",
            "category": tech,
            "price": 179,
            "stock": 65,
            "image": "images/stationery/basic-mouse-pad.png",
            "description": "Smooth desk mouse pad suitable for home, college and office use."
        },

        # ====================================================
        # LUNCH BOXES (6)
        # ====================================================
        {
            "name": "2-Compartment Lunch Box",
            "category": lunch,
            "price": 399,
            "stock": 55,
            "image": "images/stationery/lunch-box.png",
            "description": "Practical two-compartment lunch box for school, college and office meals."
        },
        {
            "name": "Insulated Lunch Bag",
            "category": lunch,
            "price": 349,
            "stock": 50,
            "image": "images/stationery/insulated-lunch-bag.png",
            "description": "Compact insulated lunch bag for carrying meals and snacks."
        },
        {
            "name": "3-Compartment Meal Box",
            "category": lunch,
            "price": 449,
            "stock": 45,
            "image": "images/stationery/3-compartment-meal-box.png",
            "description": "Three-section meal box for keeping different foods neatly separated."
        },
        {
            "name": "Compact Snack Box",
            "category": lunch,
            "price": 229,
            "stock": 70,
            "image": "images/stationery/snack-box.png",
            "description": "Small reusable box for snacks, fruits and light meals."
        },
        {
            "name": "Steel Lunch Box - 2 Tier",
            "category": lunch,
            "price": 549,
            "stock": 40,
            "image": "images/stationery/steel-lunch-box.png",
            "description": "Two-tier steel lunch box for students and office meals."
        },
        {
            "name": "Lunch Cutlery Set",
            "category": lunch,
            "price": 159,
            "stock": 85,
            "image": "images/stationery/lunch-cutlery-set.png",
            "description": "Portable spoon and fork set for everyday lunch boxes and travel."
        },

        # ====================================================
        # KEYCHAINS & ACCESSORIES (5)
        # ====================================================
        {
            "name": "Acrylic Keychain",
            "category": accessories,
            "price": 99,
            "stock": 100,
            "image": "images/stationery/acrylic-keychain.png",
            "description": "Lightweight acrylic keychain for keys, bags and everyday accessories."
        },
        {
            "name": "Multipurpose Lanyard",
            "category": accessories,
            "price": 129,
            "stock": 90,
            "image": "images/stationery/multipurpose-lanyard.png",
            "description": "Simple multipurpose lanyard for ID cards, keys and small accessories."
        },
        {
            "name": "Minimal Metal Keyring",
            "category": accessories,
            "price": 79,
            "stock": 120,
            "image": "images/stationery/metal-keyring.png",
            "description": "Simple metal keyring for keys, pouches and bags."
        },
        {
            "name": "ID Card Holder",
            "category": accessories,
            "price": 89,
            "stock": 100,
            "image": "images/stationery/id-card-holder.png",
            "description": "Clear ID card holder for college, office and events."
        },
        {
            "name": "Badge Clip Set - 3",
            "category": accessories,
            "price": 69,
            "stock": 110,
            "image": "images/stationery/badge-clip-set.png",
            "description": "Three clips for attaching badges, ID cards and small tags."
        }
    ]

    # --------------------------------------------------------
    # ADD / UPDATE NEW PRODUCTS
    # --------------------------------------------------------

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
        print("       PRINTIFY SEEDING COMPLETE")
        print("==========================================")
        print("70 stationery products added/updated.")
        print("==========================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()