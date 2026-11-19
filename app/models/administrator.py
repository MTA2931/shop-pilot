"""Administrator model with role-based access control and security tracking."""

from datetime import datetime, timezone
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class Administrator(db.Model):
    """Administrator account with RBAC support.

    Roles:
        super_admin  - Full access to all features
        admin        - Full access except super-admin-protected operations
        manager      - Limited access (orders, products, inventory, reports)
    """

    __tablename__ = "administrators"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)

    role = db.Column(db.String(20), nullable=False, default="manager", index=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    must_change_password = db.Column(
        db.Boolean, nullable=False, default=False
    )

    failed_login_attempts = db.Column(
        db.Integer, nullable=False, default=0
    )
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    current_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)
    current_login_ip = db.Column(db.String(45), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    activity_logs = db.relationship(
        "ActivityLog", backref="administrator", lazy="dynamic", cascade="all, delete-orphan"
    )

    # Role hierarchy for permission checks
    ROLE_HIERARCHY = {
        "super_admin": 3,
        "admin": 2,
        "manager": 1,
    }

    ROLE_LABELS = {
        "super_admin": "سوپر ادمین",
        "admin": "ادمین",
        "manager": "مدیر",
    }

    def set_password(self, password: str) -> None:
        """Hash and store the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check the provided password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_locked(self) -> bool:
        """Return True if the account is currently locked out."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    def record_failed_login(self) -> None:
        """Increment failed login counter and lock if threshold reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=15
            )
        db.session.commit()

    def reset_failed_logins(self) -> None:
        """Reset failed login counter after successful authentication."""
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()

    def can(self, required_role: str) -> bool:
        """Check if this administrator's role meets or exceeds required_role."""
        user_level = self.ROLE_HIERARCHY.get(self.role, 0)
        required_level = self.ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level

    def is_super_admin(self) -> bool:
        return self.role == "super_admin"

    def is_admin(self) -> bool:
        return self.role in ("super_admin", "admin")

    def is_manager(self) -> bool:
        return self.role in ("super_admin", "admin", "manager")

    @classmethod
    def ensure_default_administrator(cls):
        """Create the default administrator on first initialization if none exists."""
        if cls.query.count() == 0:
            from config import config_by_name
            import os
            config_name = os.environ.get("FLASK_CONFIG", "default")
            config_class = config_by_name.get(config_name, config_by_name["default"])

            default_username = getattr(config_class, "DEFAULT_ADMIN_USERNAME", "Admin")
            default_password = getattr(config_class, "DEFAULT_ADMIN_PASSWORD", "admin123")

            admin = cls(
                username=default_username,
                role="super_admin",
                is_active=True,
                must_change_password=True,
            )
            admin.set_password(default_password)
            db.session.add(admin)
            db.session.commit()

    @classmethod
    def count_active_super_admins(cls):
        """Return the number of active super admin accounts."""
        return cls.query.filter_by(role="super_admin", is_active=True).count()

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "role_label": self.ROLE_LABELS.get(self.role, self.role),
            "is_active": self.is_active,
            "must_change_password": self.must_change_password,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }

    def __repr__(self):
        return f"<Administrator {self.username} ({self.role})>"