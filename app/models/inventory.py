"""Inventory models: InventoryItem and InventoryMovement."""

from datetime import datetime, timezone
from app.extensions import db


class InventoryItem(db.Model):
    """Inventory item - tracks current stock per product/SKU."""

    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, unique=True, index=True
    )
    sku = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    min_threshold = db.Column(db.Integer, nullable=False, default=5)
    location = db.Column(db.String(100), nullable=True)

    last_adjusted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_adjusted_by = db.Column(db.Integer, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    product = db.relationship("Product", backref="inventory_item", lazy="select")

    def is_low_stock(self):
        return self.quantity <= self.min_threshold

    def is_out_of_stock(self):
        return self.quantity <= 0

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "sku": self.sku,
            "name": self.name,
            "quantity": self.quantity,
            "min_threshold": self.min_threshold,
            "location": self.location,
            "is_low_stock": self.is_low_stock(),
            "is_out_of_stock": self.is_out_of_stock(),
            "last_adjusted_at": (
                self.last_adjusted_at.isoformat() if self.last_adjusted_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<InventoryItem {self.sku} qty={self.quantity}>"


class InventoryMovement(db.Model):
    """Inventory movement history - every stock change is recorded."""

    __tablename__ = "inventory_movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    sku = db.Column(db.String(100), nullable=False, index=True)

    movement_type = db.Column(
        db.String(20), nullable=False, index=True
    )  # increase, decrease, adjustment

    quantity_change = db.Column(db.Integer, nullable=False)  # positive or negative
    quantity_before = db.Column(db.Integer, nullable=False)
    quantity_after = db.Column(db.Integer, nullable=False)

    reason = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )

    administrator_id = db.Column(
        db.Integer, db.ForeignKey("administrators.id"), nullable=True, index=True
    )
    administrator = db.relationship("Administrator", backref="inventory_movements", lazy="select")

    MOVEMENT_TYPES = {
        "increase": "افزایش موجودی",
        "decrease": "کاهش موجودی",
        "adjustment": "تغییر دستی",
    }

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "sku": self.sku,
            "movement_type": self.movement_type,
            "movement_type_label": self.MOVEMENT_TYPES.get(
                self.movement_type, self.movement_type
            ),
            "quantity_change": self.quantity_change,
            "quantity_before": self.quantity_before,
            "quantity_after": self.quantity_after,
            "reason": self.reason,
            "notes": self.notes,
            "administrator_id": self.administrator_id,
            "administrator_name": (
                self.administrator.username if self.administrator else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<InventoryMovement {self.sku} {self.movement_type} {self.quantity_change}>"