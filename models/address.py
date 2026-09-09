from datetime import datetime
from models import db


class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    label = db.Column(db.String(50), default="Home")          # Home / Work / Other
    contact_name = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    line1 = db.Column(db.String(255), nullable=False)
    line2 = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(12), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "label": self.label, "contact_name": self.contact_name,
            "contact_phone": self.contact_phone, "line1": self.line1, "line2": self.line2,
            "city": self.city, "state": self.state, "pincode": self.pincode,
            "is_default": self.is_default,
        }

    def full_text(self):
        parts = [self.line1, self.line2, self.city, self.state, self.pincode]
        return ", ".join(p for p in parts if p)
