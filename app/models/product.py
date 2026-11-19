"""Product model for shop product management."""

from datetime import datetime, timezone
from app.extensions import db


class Product(db.Model):
    """Represents a product in the shop inventory."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    sku = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True, index=True)

    # Price stored as integer (smallest currency unit, e.g. toman)
    price = db.Column(db.BigInteger, nullable=False, default=0)

    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    min_stock_threshold = db.Column(db.Integer, nullable=False, default=5)

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
    inventory_movements = db.relationship(
        "InventoryMovement", backref="product", lazy="dynamic", cascade="all, delete-orphan"
    )

    def is_low_stock(self):
        """Return True if stock is at or below the low-stock threshold."""
        return self.stock_quantity <= self.min_stock_threshold

    def is_out_of_stock(self):
        """Return True if stock is zero or below."""
        return self.stock_quantity <= 0

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "description": self.description,
            "category": self.category,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "min_stock_threshold": self.min_stock_threshold,
            "is_low_stock": self.is_low_stock(),
            "is_out_of_stock": self.is_out_of_stock(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Product {self.sku} ({self.name})>"