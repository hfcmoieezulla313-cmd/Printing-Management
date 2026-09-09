"""
Central configuration for the Printing Management System.
Everything environment-specific (DB, secrets, AI provider, uploads)
lives here so the rest of the app never hard-codes it.
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost/printing_management",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.environ.get("UPLOAD_FOLDER", "uploads"))
    ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 15)) * 1024 * 1024

    # AI chatbot - never exposed to the browser, read only on the server
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "anthropic")
    AI_API_KEY = os.environ.get("AI_API_KEY", "")
    AI_MODEL = os.environ.get("AI_MODEL", "claude-sonnet-4-6")
    AI_API_URL = os.environ.get("AI_API_URL", "https://api.anthropic.com/v1/messages")

    DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
