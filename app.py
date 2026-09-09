"""
Printing Management System - application entrypoint.
Run with:  python app.py
Then open: http://127.0.0.1:5000/
"""
import os
from flask import Flask, render_template
from config import Config
from models import db
from utils import current_user, current_admin


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    # ---- Blueprints -----------------------------------------------------
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.printing import printing_bp
    from routes.upload import upload_bp
    from routes.stationery import stationery_bp
    from routes.cart import cart_bp
    from routes.checkout import checkout_bp
    from routes.orders import orders_bp
    from routes.profile import profile_bp
    from routes.support import support_bp
    from routes.chatbot import chatbot_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(printing_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(stationery_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(admin_bp)

    # ---- Template globals -------------------------------------------------
    @app.context_processor
    def inject_globals():
        return {"current_user": current_user(), "current_admin": current_admin()}

    # ---- Error handlers -----------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", True))
