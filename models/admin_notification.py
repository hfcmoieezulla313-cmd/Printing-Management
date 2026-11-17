
from datetime import datetime

from models import db


class AdminNotification(db.Model):
    __tablename__ = "admin_notifications"

    id = db.Column(db.Integer, primary_key=True)

    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("admins.id"),
        nullable=False
    )

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.id"),
        nullable=True
    )

    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)

    notification_type = db.Column(
        db.String(30),
        nullable=False,
        default="general"
    )

    is_read = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def mark_as_read(self):
        self.is_read = True
