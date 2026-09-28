from sqlalchemy import inspect, text

from app import app
from models import db


with app.app_context():

    # Create any missing tables from the current models.
    db.create_all()

    inspector = inspect(db.engine)

    # ---------------------------------------------------------
    # Add photo_configuration_id to cart_items if missing
    # ---------------------------------------------------------

    cart_columns = {
        column["name"]
        for column in inspector.get_columns("cart_items")
    }

    if "photo_configuration_id" not in cart_columns:

        db.session.execute(
            text(
                """
                ALTER TABLE cart_items
                ADD COLUMN photo_configuration_id INT NULL
                """
            )
        )

        db.session.commit()

        print(
            "Added cart_items.photo_configuration_id"
        )

    else:

        print(
            "cart_items.photo_configuration_id already exists"
        )

    # ---------------------------------------------------------
    # Add foreign key if missing
    # ---------------------------------------------------------

    inspector = inspect(db.engine)

    foreign_keys = inspector.get_foreign_keys(
        "cart_items"
    )

    photo_fk_exists = any(
        fk.get("referred_table") == "photo_configurations"
        and "photo_configuration_id"
        in (fk.get("constrained_columns") or [])
        for fk in foreign_keys
    )

    if not photo_fk_exists:

        db.session.execute(
            text(
                """
                ALTER TABLE cart_items
                ADD CONSTRAINT
                fk_cart_item_photo_configuration
                FOREIGN KEY (photo_configuration_id)
                REFERENCES photo_configurations(id)
                """
            )
        )

        db.session.commit()

        print(
            "Added photo_configuration foreign key"
        )

    else:

        print(
            "Photo configuration foreign key already exists"
        )

    # ---------------------------------------------------------
    # Verify
    # ---------------------------------------------------------

    inspector = inspect(db.engine)

    tables = inspector.get_table_names()

    print()
    print("Photo configuration table:", end=" ")

    if "photo_configurations" in tables:
        print("OK")
    else:
        print("MISSING")

    cart_columns = {
        column["name"]
        for column in inspector.get_columns("cart_items")
    }

    print(
        "Photo cart column:",
        "OK"
        if "photo_configuration_id" in cart_columns
        else "MISSING"
    )