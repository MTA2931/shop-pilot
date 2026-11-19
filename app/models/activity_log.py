"""Activity log model for centralized auditing."""

from datetime import datetime, timezone
from app.extensions import db


class ActivityLog(db.Model):
    """Centralized activity log for all system actions.

    Categories:
        authentication, administrator, order, product, inventory, system, security
    """

    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)

    administrator_id = db.Column(
        db.Integer, db.ForeignKey("administrators.id"), nullable=True, index=True
    )
    administrator = db.relationship("Administrator", lazy="select", overlaps="activity_logs")

    action = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(
        db.String(30), nullable=False, index=True
    )  # authentication, administrator, order, product, inventory, system, security

    description = db.Column(db.Text, nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )

    CATEGORIES = {
        "authentication": "احراز هویت",
        "administrator": "مدیریت ادمین‌ها",
        "order": "سفارش‌ها",
        "product": "محصولات",
        "inventory": "موجودی انبار",
        "system": "سیستم",
        "security": "امنیت",
    }

    def to_dict(self):
        return {
            "id": self.id,
            "administrator_id": self.administrator_id,
            "administrator_name": (
                self.administrator.username if self.administrator else "ناشناس"
            ),
            "action": self.action,
            "category": self.category,
            "category_label": self.CATEGORIES.get(self.category, self.category),
            "description": self.description,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ActivityLog {self.category}/{self.action} at {self.created_at}>"