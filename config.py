# Copyright © 2026 MTA. All rights reserved.
# Code by MTA. Github: MTA2931

import os
from datetime import timedelta
from pathlib import Path

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Centralized application configuration.

    Sensitive values are loaded from environment variables.
    Never commit actual secrets or production credentials.
    """

    # ------------------------------------------------------------------
    # Shop / site identity
    # ------------------------------------------------------------------
    SHOP_NAME = os.environ.get("SHOP_NAME", "ShopPilot")
    SHOP_TITLE = os.environ.get("SHOP_TITLE", "ShopPilot — مدیریت فروشگاه")
    SHOP_DESCRIPTION = os.environ.get(
        "SHOP_DESCRIPTION", "پنل مدیریت هوشمند آنلاین‌شاپ"
    )

    # ------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    TESTING = False

    # ------------------------------------------------------------------
    # Security / secret key
    # ------------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-me-in-production"
    
    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    basedir = Path(__file__).resolve().parent
    instance_dir = basedir / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls):
        """Validate configuration. Call this after app creation."""
        if not cls.DEBUG and not cls.TESTING:
            if cls.SECRET_KEY == "dev-secret-key-change-me-in-production":
                import os as _os
                if not _os.environ.get("SECRET_KEY"):
                    raise RuntimeError(
                        "SECRET_KEY environment variable must be set in production."
                    )

    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get("WTF_CSRF_SECRET_KEY", SECRET_KEY)

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{(instance_dir / 'shop_pilot.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # ------------------------------------------------------------------
    # Session security
    # ------------------------------------------------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES", "120"))
    )
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    REMEMBER_COOKIE_SECURE = os.environ.get("REMEMBER_COOKIE_SECURE", "False").lower() == "true"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = os.environ.get("REMEMBER_COOKIE_SAMESITE", "Lax")

    # ------------------------------------------------------------------
    # Login security
    # ------------------------------------------------------------------
    LOGIN_RATE_LIMIT = os.environ.get("LOGIN_RATE_LIMIT", "5 per minute")
    LOGIN_LOCKOUT_DURATION_MINUTES = int(
        os.environ.get("LOGIN_LOCKOUT_DURATION_MINUTES", "15")
    )
    MAX_FAILED_LOGIN_ATTEMPTS = int(
        os.environ.get("MAX_FAILED_LOGIN_ATTEMPTS", "5")
    )

    # ------------------------------------------------------------------
    # Password security
    # ------------------------------------------------------------------
    PASSWORD_MIN_LENGTH = int(os.environ.get("PASSWORD_MIN_LENGTH", "10"))
    PASSWORD_REQUIRE_UPPER = os.environ.get("PASSWORD_REQUIRE_UPPER", "True").lower() == "true"
    PASSWORD_REQUIRE_LOWER = os.environ.get("PASSWORD_REQUIRE_LOWER", "True").lower() == "true"
    PASSWORD_REQUIRE_DIGIT = os.environ.get("PASSWORD_REQUIRE_DIGIT", "True").lower() == "true"
    PASSWORD_REQUIRE_SPECIAL = os.environ.get("PASSWORD_REQUIRE_SPECIAL", "True").lower() == "true"
    PASSWORD_REJECT_COMMON = os.environ.get("PASSWORD_REJECT_COMMON", "True").lower() == "true"
    PASSWORD_REJECT_DEFAULT = os.environ.get("PASSWORD_REJECT_DEFAULT", "True").lower() == "true"

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------
    DEFAULT_PAGE_SIZE = int(os.environ.get("DEFAULT_PAGE_SIZE", "25"))
    MAX_PAGE_SIZE = int(os.environ.get("MAX_PAGE_SIZE", "100"))

    # ------------------------------------------------------------------
    # Timezone
    # ------------------------------------------------------------------
    TIMEZONE = os.environ.get("TIMEZONE", "Asia/Tehran")

    # ------------------------------------------------------------------
    # File upload (future use)
    # ------------------------------------------------------------------
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "16")) * 1024 * 1024
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(basedir, "instance", "uploads"))

    # ------------------------------------------------------------------
    # Default administrator (first initialization)
    # ------------------------------------------------------------------
    DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "Admin")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123")


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "instance", "shop_pilot_test.db")
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    PASSWORD_REJECT_DEFAULT = False  # allow simpler passwords in tests


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}