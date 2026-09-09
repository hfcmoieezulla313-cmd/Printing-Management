from models import db


class Category(db.Model):
    """
    A single categories table used for BOTH printing services and
    stationery, distinguished by `kind`. Keeps category management in
    one admin screen instead of two.
    """
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    kind = db.Column(db.String(20), nullable=False)   # "printing" or "stationery"
    icon = db.Column(db.String(50), default="folder")
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    printing_services = db.relationship("PrintingService", backref="category", lazy=True)
    stationery_products = db.relationship("StationeryProduct", backref="category", lazy=True)
