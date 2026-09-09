from datetime import datetime
from models import db

ORDER_STATUSES = [
    "Pending", "Confirmed", "Printing", "Ready for Delivery",
    "Out for Delivery", "Delivered", "Cancelled",
]


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey("addresses.id"), nullable=False)
    coupon_id = db.Column(db.Integer, db.ForeignKey("coupons.id"), nullable=True)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    delivery_charge = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    payment_method = db.Column(db.String(20), nullable=False, default="COD")  # COD / ONLINE_PLACEHOLDER
    status = db.Column(db.String(30), nullable=False, default="Pending")

    contact_name = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    address = db.relationship("Address")
    coupon = db.relationship("Coupon")
    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    def status_index(self):
        try:
            return ORDER_STATUSES.index(self.status)
        except ValueError:
            return 0


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # PRINTING / STATIONERY
    name_snapshot = db.Column(db.String(200), nullable=False)
    details_snapshot = db.Column(db.Text)   # human-readable config, frozen at order time
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    line_total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
