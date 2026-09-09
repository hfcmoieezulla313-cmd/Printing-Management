"""
Shared SQLAlchemy instance. All model modules import `db` from here
so there is exactly one metadata registry for the whole app.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models AFTER db is defined so they can attach to it.
# Also re-export them here so `from models import User, Order, ...` works.
from models.user import User            # noqa: E402
from models.admin import Admin          # noqa: E402
from models.address import Address      # noqa: E402
from models.category import Category    # noqa: E402
from models.printing_service import PrintingService   # noqa: E402
from models.stationery_product import StationeryProduct  # noqa: E402
from models.document import UploadedDocument            # noqa: E402
from models.print_configuration import PrintConfiguration  # noqa: E402
from models.cart import Cart, CartItem  # noqa: E402
from models.order import Order, OrderItem  # noqa: E402
from models.coupon import Coupon        # noqa: E402
from models.complaint import Complaint  # noqa: E402
from models.notification import Notification  # noqa: E402
from models.chat import ChatSession, ChatMessage  # noqa: E402
from models.setting import Setting      # noqa: E402

__all__ = [
    "db", "User", "Admin", "Address", "Category", "PrintingService",
    "StationeryProduct", "UploadedDocument", "PrintConfiguration",
    "Cart", "CartItem", "Order", "OrderItem", "Coupon", "Complaint",
    "Notification", "ChatSession", "ChatMessage", "Setting",
]
