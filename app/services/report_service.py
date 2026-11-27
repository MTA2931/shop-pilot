"""Reporting service for generating sales, order, product, and inventory reports."""

from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.order import Order
from app.models.product import Product
from app.models.inventory import InventoryItem, InventoryMovement


class ReportService:
    @staticmethod
    def get_sales_report(date_from, date_to):
        """Sales report grouped by date."""
        from sqlalchemy import func
        results = (
            db.session.query(
                func.date(Order.created_at).label("date"),
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_amount"),
            )
            .filter(Order.created_at >= date_from)
            .filter(Order.created_at <= date_to)
            .filter(Order.status == "completed")
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at).asc())
            .all()
        )
        return [
            {
                "date": r.date if r.date else None,
                "order_count": r.order_count,
                "total_amount": r.total_amount,
            }
            for r in results
        ]

    @staticmethod
    def get_order_report(date_from, date_to):
        """Order report by status."""
        from sqlalchemy import func
        results = (
            db.session.query(
                Order.status,
                func.count(Order.id).label("count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_amount"),
            )
            .filter(Order.created_at >= date_from)
            .filter(Order.created_at <= date_to)
            .group_by(Order.status)
            .all()
        )
        status_labels = {
            "pending": "در انتظار پرداخت",
            "processing": "در حال پردازش",
            "completed": "پرداخت‌شده",
            "cancelled": "لغو‌شده",
        }
        return [
            {
                "status": r.status,
                "status_label": status_labels.get(r.status, r.status),
                "count": r.count,
                "total_amount": r.total_amount,
            }
            for r in results
        ]

    @staticmethod
    def get_product_report():
        """Product report by category."""
        from sqlalchemy import func
        results = (
            db.session.query(
                Product.category,
                func.count(Product.id).label("product_count"),
                func.coalesce(func.sum(Product.stock_quantity), 0).label("total_stock"),
                func.coalesce(func.sum(Product.price * Product.stock_quantity), 0).label("total_value"),
            )
            .group_by(Product.category)
            .all()
        )
        return [
            {
                "category": r.category or "بدون دسته‌بندی",
                "product_count": r.product_count,
                "total_stock": r.total_stock,
                "total_value": r.total_value,
            }
            for r in results
        ]

    @staticmethod
    def get_inventory_report():
        """Inventory report summary."""
        total_items = db.session.query(db.func.count(InventoryItem.id)).scalar() or 0
        total_quantity = db.session.query(db.func.coalesce(db.func.sum(InventoryItem.quantity), 0)).scalar() or 0
        low_stock = (
            db.session.query(db.func.count(InventoryItem.id))
            .filter(InventoryItem.quantity <= InventoryItem.min_threshold)
            .scalar()
            or 0
        )
        out_of_stock = (
            db.session.query(db.func.count(InventoryItem.id))
            .filter(InventoryItem.quantity <= 0)
            .scalar()
            or 0
        )

        return {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
        }

    @staticmethod
    def get_performance_report(date_from, date_to):
        """Performance report with key metrics."""
        total_orders = (
            db.session.query(db.func.count(Order.id))
            .filter(Order.created_at >= date_from)
            .filter(Order.created_at <= date_to)
            .scalar()
            or 0
        )
        completed_orders = (
            db.session.query(db.func.count(Order.id))
            .filter(Order.created_at >= date_from)
            .filter(Order.created_at <= date_to)
            .filter(Order.status == "completed")
            .scalar()
            or 0
        )
        total_revenue = (
            db.session.query(db.func.coalesce(db.func.sum(Order.total_amount), 0))
            .filter(Order.created_at >= date_from)
            .filter(Order.created_at <= date_to)
            .filter(Order.status == "completed")
            .scalar()
            or 0
        )

        conversion_rate = (
            round((completed_orders / total_orders) * 100, 2) if total_orders > 0 else 0
        )
        average_order_value = (
            round(total_revenue / completed_orders, 2) if completed_orders > 0 else 0
        )

        return {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "total_revenue": total_revenue,
            "conversion_rate": conversion_rate,
            "average_order_value": average_order_value,
        }

    @staticmethod
    def get_inventory_movements_report(date_from, date_to):
        """Inventory movements report."""
        from sqlalchemy import func
        results = (
            db.session.query(
                InventoryMovement.movement_type,
                func.count(InventoryMovement.id).label("count"),
                func.coalesce(func.sum(InventoryMovement.quantity_change), 0).label("total_change"),
            )
            .filter(InventoryMovement.created_at >= date_from)
            .filter(InventoryMovement.created_at <= date_to)
            .group_by(InventoryMovement.movement_type)
            .all()
        )
        type_labels = {
            "increase": "افزایش",
            "decrease": "کاهش",
            "adjustment": "تغییر دستی",
        }
        return [
            {
                "movement_type": r.movement_type,
                "movement_type_label": type_labels.get(r.movement_type, r.movement_type),
                "count": r.count,
                "total_change": r.total_change,
            }
            for r in results
        ]