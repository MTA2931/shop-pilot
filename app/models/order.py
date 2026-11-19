"""Order model for shop order management."""

from datetime import datetime, timezone
from app.extensions import db


class Order(db.Model):
    """Represents a customer order in the shop."""

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(120), nullable=False, index=True)
    customer_phone = db.Column(db.String(30), nullable=True)
    customer_address = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)  # Order description / products summary

    # Monetary value stored as integer (smallest currency unit, e.g. toman)
    total_amount = db.Column(db.BigInteger, nullable=False, default=0)

    status = db.Column(
        db.String(20), nullable=False, default="pending", index=True
    )  # pending, processing, completed, cancelled

    channel = db.Column(
        db.String(20), nullable=True, default="website"
    )  # website, instagram, phone, etc.

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    administrator_id = db.Column(
        db.Integer, db.ForeignKey("administrators.id"), nullable=True, index=True
    )
    administrator = db.relationship("Administrator", backref="orders", lazy="select")

    # Order statuses
    STATUSES = {
        "pending": "در انتظار پرداخت",
        "processing": "در حال پردازش",
        "completed": "پرداخت‌شده",
        "cancelled": "لغو‌شده",
    }

    STATUS_LABELS = {
        "pending": "در انتظار پرداخت",
        "processing": "در حال پردازش",
        "completed": "پرداخت‌شده",
        "cancelled": "لغو‌شده",
    }

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "customer_address": self.customer_address,
            "description": self.description,
            "total_amount": self.total_amount,
            "status": self.status,
            "status_label": self.STATUS_LABELS.get(self.status, self.status),
            "channel": self.channel,
            "administrator_id": self.administrator_id,
            "administrator_name": (
                self.administrator.username if self.administrator else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Order {self.order_number} ({self.status})>"