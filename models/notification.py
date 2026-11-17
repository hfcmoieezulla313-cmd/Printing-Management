
from datetime import datetime
from models import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)

    # order, complaint, general
    notification_type = db.Column(
        db.String(30),
        nullable=False,
        default="general"
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def mark_as_read(self):
        self.is_read = True

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }
