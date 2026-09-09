from datetime import datetime
from models import db


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship("CartItem", backref="cart", lazy=True, cascade="all, delete-orphan")

    def subtotal(self):
        return sum((item.line_total() for item in self.items), 0)


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # PRINTING / STATIONERY

    # Only one of these is populated depending on item_type
    print_configuration_id = db.Column(db.Integer, db.ForeignKey("print_configurations.id"), nullable=True)
    stationery_product_id = db.Column(db.Integer, db.ForeignKey("stationery_products.id"), nullable=True)

    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)  # snapshot at add-to-cart time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    print_configuration = db.relationship("PrintConfiguration")
    stationery_product = db.relationship("StationeryProduct")

    def display_name(self):
        if self.item_type == "PRINTING" and self.print_configuration:
            svc = self.print_configuration.printing_service
            return svc.name if svc else "Printing item"
        if self.item_type == "STATIONERY" and self.stationery_product:
            return self.stationery_product.name
        return "Item"

    def line_total(self):
        if self.item_type == "PRINTING" and self.print_configuration:
            # printing quantity is already baked into computed_total (copies),
            # so line total is simply that configuration total.
            return float(self.print_configuration.computed_total)
        return float(self.unit_price) * self.quantity
