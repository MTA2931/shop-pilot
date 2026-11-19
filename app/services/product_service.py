"""Product business logic service."""

from app.extensions import db
from app.models.product import Product
from app.services.logging_service import log_activity


class ProductService:
    @staticmethod
    def create_product(data: dict, administrator_id: int = None) -> tuple:
        """Create a new product.

        Returns (product, error_message).
        """
        sku = data.get("sku", "").strip().upper()
        if Product.query.filter_by(sku=sku).first():
            return None, "کد محصول (SKU) تکراری است."

        price = int(data.get("price", 0) or 0)
        if price < 0:
            return None, "قیمت نمی‌تواند منفی باشد."

        stock = int(data.get("stock_quantity", 0) or 0)
        if stock < 0:
            return None, "موجودی نمی‌تواند منفی باشد."

        min_threshold = int(data.get("min_stock_threshold", 5) or 5)
        if min_threshold < 0:
            return None, "حد حداقل موجودی نمی‌تواند منفی باشد."

        product = Product(
            name=data.get("name", "").strip(),
            sku=sku,
            description=data.get("description", "").strip() or None,
            category=data.get("category", "").strip() or None,
            price=price,
            stock_quantity=stock,
            min_stock_threshold=min_threshold,
        )
        db.session.add(product)
        db.session.commit()

        # Create initial inventory item
        from app.models.inventory import InventoryItem, InventoryMovement
        inventory_item = InventoryItem(
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            quantity=product.stock_quantity,
            min_threshold=product.min_stock_threshold,
        )
        db.session.add(inventory_item)

        # Record initial stock movement
        if stock > 0:
            movement = InventoryMovement(
                product_id=product.id,
                sku=product.sku,
                movement_type="increase",
                quantity_change=stock,
                quantity_before=0,
                quantity_after=stock,
                reason="افزایش اولیه موجودی",
                administrator_id=administrator_id,
            )
            db.session.add(movement)
            inventory_item.last_adjusted_at = product.created_at
            inventory_item.last_adjusted_by = administrator_id

        db.session.commit()

        log_activity(
            administrator_id=administrator_id,
            action="create_product",
            category="product",
            description=f"Product created: {product.name} (SKU: {product.sku})",
            entity_type="product",
            entity_id=product.id,
        )

        return product, None

    @staticmethod
    def update_product(product: Product, data: dict, administrator_id: int = None) -> tuple:
        """Update an existing product.

        Returns (product, error_message).
        """
        old_sku = product.sku
        new_sku = data.get("sku", product.sku).strip().upper()

        if new_sku != old_sku:
            existing = Product.query.filter_by(sku=new_sku).first()
            if existing:
                return None, "کد محصول (SKU) تکراری است."

        price = int(data.get("price", product.price) or 0)
        if price < 0:
            return None, "قیمت نمی‌تواند منفی باشد."

        stock = int(data.get("stock_quantity", product.stock_quantity) or 0)
        if stock < 0:
            return None, "موجودی نمی‌تواند منفی باشد."

        min_threshold = int(data.get("min_stock_threshold", product.min_stock_threshold) or 5)
        if min_threshold < 0:
            return None, "حد حداقل موجودی نمی‌تواند منفی باشد."

        old_stock = product.stock_quantity

        product.sku = new_sku
        product.name = data.get("name", product.name).strip()
        product.description = data.get("description", product.description).strip() or None
        product.category = data.get("category", product.category).strip() or None
        product.price = price
        product.stock_quantity = stock
        product.min_stock_threshold = min_threshold

        # Update inventory item
        from app.models.inventory import InventoryItem, InventoryMovement
        inventory_item = InventoryItem.query.filter_by(product_id=product.id).first()
        if inventory_item:
            inventory_item.sku = new_sku
            inventory_item.name = product.name
            inventory_item.quantity = stock
            inventory_item.min_threshold = min_threshold
            inventory_item.last_adjusted_at = product.updated_at
            inventory_item.last_adjusted_by = administrator_id

            # Record stock movement if quantity changed
            if stock != old_stock:
                movement = InventoryMovement(
                    product_id=product.id,
                    sku=new_sku,
                    movement_type="adjustment",
                    quantity_change=stock - old_stock,
                    quantity_before=old_stock,
                    quantity_after=stock,
                    reason="تغییر موجودی از طریق ویرایش محصول",
                    administrator_id=administrator_id,
                )
                db.session.add(movement)

        db.session.commit()

        log_activity(
            administrator_id=administrator_id,
            action="update_product",
            category="product",
            description=f"Product updated: {product.name} (SKU: {product.sku})",
            entity_type="product",
            entity_id=product.id,
        )

        return product, None

    @staticmethod
    def delete_product(product: Product, administrator_id: int = None) -> bool:
        """Delete a product and its inventory records."""
        product_name = product.name
        product_sku = product.sku
        product_id = product.id

        db.session.delete(product)
        db.session.commit()

        log_activity(
            administrator_id=administrator_id,
            action="delete_product",
            category="product",
            description=f"Product deleted: {product_name} (SKU: {product_sku})",
            entity_type="product",
            entity_id=product_id,
        )
        return True

    @staticmethod
    def get_product_by_id(product_id: int) -> Product:
        return Product.query.get(product_id)

    @staticmethod
    def get_products(
        page=1,
        per_page=25,
        search=None,
        category_filter=None,
        stock_filter=None,
        sort_by="created_at",
        sort_order="desc",
    ):
        """Get paginated products with filtering and sorting."""
        query = Product.query

        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    Product.name.ilike(like),
                    Product.sku.ilike(like),
                    Product.description.ilike(like),
                )
            )

        if category_filter:
            query = query.filter_by(category=category_filter)

        if stock_filter == "low_stock":
            query = query.filter(Product.stock_quantity <= Product.min_stock_threshold)
        elif stock_filter == "out_of_stock":
            query = query.filter(Product.stock_quantity <= 0)
        elif stock_filter == "in_stock":
            query = query.filter(Product.stock_quantity > Product.min_stock_threshold)

        if sort_order == "asc":
            query = query.order_by(getattr(Product, sort_by).asc())
        else:
            query = query.order_by(getattr(Product, sort_by).desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_stats():
        """Get product statistics."""
        total = Product.query.count()
        low_stock = Product.query.filter(
            Product.stock_quantity <= Product.min_stock_threshold
        ).count()
        out_of_stock = Product.query.filter(Product.stock_quantity <= 0).count()

        return {
            "total": total,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
        }

    @staticmethod
    def get_categories():
        """Get distinct product categories."""
        return (
            db.session.query(Product.category)
            .filter(Product.category.isnot(None))
            .distinct()
            .all()
        )