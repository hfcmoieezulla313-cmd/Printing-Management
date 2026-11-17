
"""
Shared SQLAlchemy instance. All model modules import db from here.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models AFTER db is defined.
from models.user import User
from models.admin import Admin
from models.address import Address
from models.category import Category
from models.printing_service import PrintingService
from models.document import UploadedDocument
from models.print_configuration import PrintConfiguration
from models.photo_configuration import PhotoConfiguration
from models.cart import Cart, CartItem
from models.order import Order, OrderItem
from models.coupon import Coupon
from models.complaint import Complaint
from models.notification import Notification
from models.admin_notification import AdminNotification
from models.chat import ChatSession, ChatMessage
from models.setting import Setting

__all__ = [
    "db",
    "User",
    "Admin",
    "Address",
    "Category",
    "PrintingService",
    "UploadedDocument",
    "PrintConfiguration",
    "PhotoConfiguration",
    "Cart",
    "CartItem",
    "Order",
    "OrderItem",
    "Coupon",
    "Complaint",
    "Notification",
    "AdminNotification",
    "ChatSession",
    "ChatMessage",
    "Setting",
]
