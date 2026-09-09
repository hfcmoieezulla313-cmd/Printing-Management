from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db


class Admin(db.Model):
    """
    Administrator account. Deliberately a SEPARATE table/model from User
    so a customer can never self-elevate into an admin - admin rows are
    only ever created by database/seed.py or a protected internal process.
    """
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)
