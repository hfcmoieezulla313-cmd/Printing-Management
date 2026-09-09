from datetime import datetime
from models import db


class PrintingService(db.Model):
    """
    Printing service catalog. Prices live HERE in the database - never
    hard-coded in routes/templates/chatbot. Admin edits them through
    /admin/printing-services and every price calculation reads from
    this table via services/pricing_service.py.
    """
    __tablename__ = "printing_services"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.Text)
    paper_size = db.Column(db.String(10))          # A4 / A3 / null (generic, e.g. Scanning)
    print_type = db.Column(db.String(10))           # BW / COLOR / null
    price_per_page = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    double_side_extra = db.Column(db.Numeric(10, 2), default=0)   # extra per page for double side
    is_configurable = db.Column(db.Boolean, default=True)  # show full config screen vs flat price
    flat_price = db.Column(db.Numeric(10, 2))         # used for things like "Spiral Binding"
    image = db.Column(db.String(255), default="printing/default.svg")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "slug": self.slug,
            "description": self.description, "paper_size": self.paper_size,
            "print_type": self.print_type,
            "price_per_page": float(self.price_per_page or 0),
            "double_side_extra": float(self.double_side_extra or 0),
            "is_configurable": self.is_configurable,
            "flat_price": float(self.flat_price) if self.flat_price is not None else None,
            "image": self.image,
        }
