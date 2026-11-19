"""Inventory business logic service."""

from app.extensions import db
from app.models.inventory import InventoryItem, InventoryMovement
from app.models.product import Product
from app.services.logging_service import log_activity


class InventoryService:
    @staticmethod
    def adjust_stock(
        product_id: int,
        quantity_change: int,
        movement_type: str,
        reason: str,
        notes: str = None,
        administrator_id: int = None,
    ) -> tuple:
        """Adjust stock for a product and record the movement.

        Returns (inventory_item, error_message).
        """
        valid_types = ["increase", "decrease", "adjustment"]
        if movement_type not in valid_types:
            return None, "نوع تغییر نامعتبر است."

        product = Product.query.get(product_id)
        if not product:
            return None, "محصول یافت نشد."

        inventory_item = InventoryItem.query.filter_by(product_id=product_id).first()
        if not inventory_item:
            inventory_item = InventoryItem(
                product_id=product_id,
                sku=product.sku,
                name=product.name,
                quantity=0,
                min_threshold=product.min_stock_threshold,
            )
            db.session.add(inventory_item)
            db.session.flush()

        quantity_before = inventory_item.quantity
        quantity_after = quantity_before + quantity_change

        if quantity_after < 0:
            return None, "موجودی نمی‌تواند منفی شود."

        # Update inventory item
        inventory_item.quantity = quantity_after
        inventory_item.last_adjusted_at = db.func.current_timestamp()
        inventory_item.last_adjusted_by = administrator_id

        # Update product stock as well
        product.stock_quantity = quantity_after

        # Record movement
        movement = InventoryMovement(
            product_id=product_id,
            sku=product.sku,
            movement_type=movement_type,
            quantity_change=quantity_change,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reason=reason,
            notes=notes,
            administrator_id=administrator_id,
        )
        db.session.add(movement)
        db.session.commit()

        log_activity(
            administrator_id=administrator_id,
            action=f"inventory_{movement_type}",
            category="inventory",
            description=f"Stock {movement_type} for {product.name} (SKU: {product.sku}): {quantity_before} → {quantity_after}",
            entity_type="inventory_item",
            entity_id=inventory_item.id,
        )

        return inventory_item, None

    @staticmethod
    def get_inventory_items(
        page=1,
        per_page=25,
        search=None,
        stock_filter=None,
        sort_by="name",
        sort_order="asc",
    ):
        """Get paginated inventory items."""
        query = InventoryItem.query

        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    InventoryItem.name.ilike(like),
                    InventoryItem.sku.ilike(like),
                )
            )

        if stock_filter == "low_stock":
            query = query.filter(InventoryItem.quantity <= InventoryItem.min_threshold)
        elif stock_filter == "out_of_stock":
            query = query.filter(InventoryItem.quantity <= 0)
        elif stock_filter == "in_stock":
            query = query.filter(InventoryItem.quantity > InventoryItem.min_threshold)

        if sort_order == "asc":
            query = query.order_by(getattr(InventoryItem, sort_by).asc())
        else:
            query = query.order_by(getattr(InventoryItem, sort_by).desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_movements(
        page=1,
        per_page=25,
        search=None,
        movement_type=None,
        date_from=None,
        date_to=None,
    ):
        """Get paginated inventory movements."""
        query = InventoryMovement.query

        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    InventoryMovement.sku.ilike(like),
                    InventoryMovement.reason.ilike(like),
                )
            )

        if movement_type:
            query = query.filter_by(movement_type=movement_type)

        if date_from:
            query = query.filter(InventoryMovement.created_at >= date_from)
        if date_to:
            query = query.filter(InventoryMovement.created_at <= date_to)

        query = query.order_by(InventoryMovement.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_stats():
        """Get inventory statistics."""
        total_items = db.session.query(db.func.count(InventoryItem.id)).scalar() or 0
        total_quantity = db.session.query(db.func.coalesce(db.func.sum(InventoryItem.quantity), 0)).scalar() or 0
        low_stock = db.session.query(db.func.count(InventoryItem.id)).filter(
            InventoryItem.quantity <= InventoryItem.min_threshold
        ).scalar() or 0
        out_of_stock = db.session.query(db.func.count(InventoryItem.id)).filter(
            InventoryItem.quantity <= 0
        ).scalar() or 0

        return {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
        }