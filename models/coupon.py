from datetime import datetime
from models import db


class Coupon(db.Model):
    __tablename__ = "coupons"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    discount_type = db.Column(db.String(10), nullable=False)   # PERCENT / FIXED
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    minimum_order_value = db.Column(db.Numeric(10, 2), default=0)
    maximum_discount = db.Column(db.Numeric(10, 2), nullable=True)  # cap for PERCENT coupons
    active = db.Column(db.Boolean, default=True)
    expiry_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid_now(self):
        if not self.active:
            return False
        if self.expiry_date and datetime.utcnow() > self.expiry_date:
            return False
        return True
