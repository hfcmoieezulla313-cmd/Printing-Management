from datetime import datetime
from models import db


class UploadedDocument(db.Model):
    """Metadata for a file a customer uploaded for printing. The actual
    bytes live under UPLOAD_FOLDER on disk under a random secure name;
    only that name + original filename are stored here."""
    __tablename__ = "uploaded_documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    file_extension = db.Column(db.String(10), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False)
    page_count = db.Column(db.Integer, default=1)   # best-effort, editable by user for pricing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    print_configurations = db.relationship("PrintConfiguration", backref="document", lazy=True)
