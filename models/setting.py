from models import db


class Setting(db.Model):
    """Simple key/value store for admin-editable business settings
    (minimum_order_value, delivery_charge, support contacts, etc.)
    so nothing important is hard-coded in Python files."""
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))

    @staticmethod
    def get(key, default=None):
        row = Setting.query.filter_by(key=key).first()
        return row.value if row else default

    @staticmethod
    def get_float(key, default=0.0):
        val = Setting.get(key)
        try:
            return float(val) if val is not None else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def set(key, value, description=None):
        row = Setting.query.filter_by(key=key).first()
        if row:
            row.value = str(value)
            if description:
                row.description = description
        else:
            row = Setting(key=key, value=str(value), description=description)
            db.session.add(row)
        return row
