from datetime import datetime
from models import db


class PrintConfiguration(db.Model):
    """A saved printing configuration (paper size/type/side/copies/binding)
    for one uploaded document, priced server-side and referenced by a
    cart item."""
    __tablename__ = "print_configurations"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("uploaded_documents.id"), nullable=False)
    printing_service_id = db.Column(db.Integer, db.ForeignKey("printing_services.id"), nullable=False)
    paper_size = db.Column(db.String(10), nullable=False, default="A4")
    print_type = db.Column(db.String(10), nullable=False, default="BW")
    print_side = db.Column(db.String(10), nullable=False, default="SINGLE")  # SINGLE / DOUBLE
    copies = db.Column(db.Integer, nullable=False, default=1)
    binding = db.Column(db.String(20), default="NONE")  # NONE / SPIRAL
    page_count = db.Column(db.Integer, nullable=False, default=1)
    computed_total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    printing_service = db.relationship("PrintingService")
