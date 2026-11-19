"""Order business logic service."""

from app.extensions import db
from app.models.order import Order
from app.services.logging_service import log_activity


class OrderService:
    @staticmethod
    def create_order(data: dict, administrator_id: int = None) -> tuple:
        """Create a new order.

        Returns (order, error_message).
        """
        last_order = Order.query.order_by(Order.id.desc()).first()
        if last_order:
            try:
                last_num = int(last_order.order_number.replace("#", ""))
                order_number = f"#{last_num + 1}"
            except (ValueError, AttributeError):
                order_number = f"#{Order.query.count() + 1}"
        else:
            order_number = "#1001"

        total_amount = int(data.get("total_amount", 0) or 0)
        if total_amount < 0:
            return None, "مبلغ سفارش نمی‌تواند منفی باشد."

        order = Order(
            order_number=order_number,
            customer_name=data.get("customer_name", "").strip(),
            customer_phone=data.get("customer_phone", "").strip() or None,
            customer_address=data.get("customer_address", "").strip() or None,
            description=data.get("description", "").strip() or None,
            total_amount=total_amount,
            status=data.get("status", "pending"),
            channel=data.get("channel", "website"),
            administrator_id=administrator_id,
        )
        db.session.add(order)
        db.session.commit()

        log_activity(
            administrator_id=administrator_id,
            action="create_order",
            category="order",
            description=f"Order created: {order.order_number}",
            entity_type="order",
            entity_id=order.id,
        )

        return order, None

    @staticmethod
    def update_order(order: Order, data: dict, administrator_id: int = None) -> tuple:
        """Update an existing order.

        Returns (order, error_message).
        """
        old_status = order.status

        order.customer_name = data.get("customer_name", order.customer_name).strip()
        order.customer_phone = data.get("customer_phone", order.customer_phone).strip() or None
        order.customer_address = data.get("customer_address", order.customer_address).strip() or None
        order.description = data.get("description", order.description).strip() or None
        order.total_amount = int(data.get("total_amount", order.total_amount) or 0)
        order.status = data.get("status", order.status)
        order.channel = data.get("channel", order.channel)

        if order.total_amount < 0:
            return None, "مبلغ سفارش نمی‌تواند منفی باشد."

        db.session.commit()

        log_activity(
            administrator_id=administrator_id,
            action="update_order",
            category="order",
            description=f"Order updated: {order.order_number}" + (
                f" (status changed from {old_status} to {order.status})"
                if old_status != order.status else ""
            ),
            entity_type="order",
            entity_id=order.id,
        )

        return order, None

    @staticmethod
    def change_status(order: Order, new_status: str, administrator_id: int = None) -> tuple:
        """Change only the order status.

        Returns (order, error_message).
        """
        valid_statuses = ["pending", "processing", "completed", "cancelled"]
        if new_status not in valid_statuses:
            return None, "وضعیت نامعتبر است."

        old_status = order.status
        order.status = new_status
        db.session.commit()

        log_activity(
            administrator_id=administrator_id,
            action="change_order_status",
            category="order",
            description=f"Order {order.order_number} status changed from {old_status} to {new_status}",
            entity_type="order",
            entity_id=order.id,
        )

        return order, None

    @staticmethod
    def delete_order(order: Order, administrator_id: int = None) -> bool:
        """Delete an order. Returns True on success."""
        order_number = order.order_number
        order_id = order.id
        db.session.delete(order)
        db.session.commit()

        log_activity(
            administrator_id=administrator_id,
            action="delete_order",
            category="order",
            description=f"Order deleted: {order_number}",
            entity_type="order",
            entity_id=order_id,
        )
        return True

    @staticmethod
    def get_order_by_id(order_id: int) -> Order:
        return Order.query.get(order_id)

    @staticmethod
    def get_orders(
        page=1,
        per_page=25,
        search=None,
        status_filter=None,
        date_from=None,
        date_to=None,
        sort_by="created_at",
        sort_order="desc",
    ):
        """Get paginated orders with filtering and sorting."""
        query = Order.query

        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    Order.customer_name.ilike(like),
                    Order.order_number.ilike(like),
                    Order.description.ilike(like),
                )
            )

        if status_filter:
            query = query.filter_by(status=status_filter)

        if date_from:
            query = query.filter(Order.created_at >= date_from)
        if date_to:
            query = query.filter(Order.created_at <= date_to)

        if sort_order == "asc":
            query = query.order_by(getattr(Order, sort_by).asc())
        else:
            query = query.order_by(getattr(Order, sort_by).desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_stats():
        """Get dashboard order statistics."""
        total = Order.query.count()
        pending = Order.query.filter_by(status="pending").count()
        processing = Order.query.filter_by(status="processing").count()
        completed = Order.query.filter_by(status="completed").count()
        cancelled = Order.query.filter_by(status="cancelled").count()

        total_sales = db.session.query(db.func.coalesce(db.func.sum(Order.total_amount), 0)).scalar() or 0

        return {
            "total": total,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "cancelled": cancelled,
            "total_sales": total_sales,
        }

    @staticmethod
    def get_recent_orders(limit=5):
        return Order.query.order_by(Order.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_sales_by_date(date_from, date_to):
        """Get sales grouped by date for charts."""
        from sqlalchemy import func
        results = (
            db.session.query(
                func.date(Order.created_at).label("date"),
                func.count(Order.id).label("count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amount"),
            )
            .filter(Order.created_at >= date_from)
            .filter(Order.created_at <= date_to)
            .filter(Order.status == "completed")
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at).asc())
            .all()
        )
        return results