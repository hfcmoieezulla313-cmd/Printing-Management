from datetime import datetime

from models import db


class PhotoConfiguration(db.Model):
    """
    Stores the configuration and server-calculated price for
    Photo and Passport Photo cart items.
    """

    __tablename__ = "photo_configurations"

    id = db.Column(db.Integer, primary_key=True)

    # Uploaded photo file
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("uploaded_documents.id"),
        nullable=False
    )

    # PHOTO or PASSPORT
    photo_type = db.Column(
        db.String(20),
        nullable=False
    )

    # Used for normal Photo printing.
    # Examples: 4x6, 5x7, 6x8
    photo_size = db.Column(
        db.String(20),
        nullable=True
    )

    # Used for normal Photo printing.
    # Examples: NONE, WHITE, BLACK
    frame = db.Column(
        db.String(20),
        nullable=True,
        default="NONE"
    )

    # Number of printed copies / passport photos
    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    # Price calculated by the server
    computed_total = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    document = db.relationship("UploadedDocument")

    def display_name(self):
        if self.photo_type == "PASSPORT":
            return "Passport Photo"

        size = self.photo_size or "Photo"
        return f"Photo - {size}"