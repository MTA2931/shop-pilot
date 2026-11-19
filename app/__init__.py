"""ShopPilot Flask application factory."""

import os
from flask import Flask, redirect, url_for, render_template, flash, g, request
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFError
from werkzeug.security import check_password_hash

from config import config_by_name
from app.extensions import db, migrate, login_manager, limiter
from app.models.administrator import Administrator
from app.services.logging_service import log_activity


def create_app(config_name=None):
    """Application factory pattern.

    Creates and configures the Flask application instance.
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "default")

    from config import config_by_name as config_classes

    config_class = config_classes.get(config_name, config_classes["default"])

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Validate configuration
    config_class.validate()

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.orders import orders_bp
    from app.routes.products import products_bp
    from app.routes.inventory import inventory_bp
    from app.routes.reports import reports_bp
    from app.routes.administrators import administrators_bp
    from app.routes.logs import logs_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(administrators_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(settings_bp)

    # ------------------------------------------------------------------
    # Template context processors
    # ------------------------------------------------------------------
    @app.context_processor
    def inject_config():
        return {
            "shop_name": app.config.get("SHOP_NAME", "ShopPilot"),
            "shop_title": app.config.get("SHOP_TITLE", "ShopPilot"),
            "shop_description": app.config.get("SHOP_DESCRIPTION", ""),
        }

    # ------------------------------------------------------------------
    # Flask-Login user loader
    # ------------------------------------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        return Administrator.query.get(int(user_id))

    login_manager.login_view = "auth.login"
    login_manager.login_message = "لطفا برای دسترسی به این صفحه وارد شوید."
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    # ------------------------------------------------------------------
    # Before-request hooks
    # ------------------------------------------------------------------
    @app.before_request
    def before_request():
        g.shop_name = app.config.get("SHOP_NAME", "ShopPilot")

        # Force password change for default administrator on first login
        if current_user.is_authenticated:
            if getattr(current_user, "must_change_password", False):
                allowed_endpoints = {
                    "auth.change_password",
                    "auth.logout",
                    "static",
                }
                if request.endpoint not in allowed_endpoints:
                    return redirect(url_for("auth.change_password"))

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(CSRFError)
    def csrf_error(reason):
        log_activity(
            administrator_id=current_user.id if current_user.is_authenticated else None,
            action="csrf_validation_failed",
            category="security",
            description=f"CSRF validation failed: {reason}",
            entity_id=None,
        )
        return render_template("errors/403.html", message="خطای اعتبارسنجی CSRF. لطفا صفحه را بازخوانی کنید و دوباره تلاش کنید."), 403

    # ------------------------------------------------------------------
    # Initialize database and create default administrator
    # ------------------------------------------------------------------
    with app.app_context():
        # Import all models to ensure they are registered with SQLAlchemy
        from app.models import administrator, order, product, inventory, activity_log  # noqa: F401

        db.create_all()

        # Create default administrator if none exists
        Administrator.ensure_default_administrator()

    return app