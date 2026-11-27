"""Dashboard routes."""

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.inventory_service import InventoryService
from app.models.order import Order

from datetime import date

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    """Dashboard overview with real statistics and charts."""
    order_stats = OrderService.get_stats()
    product_stats = ProductService.get_stats()
    inventory_stats = InventoryService.get_stats()

    recent_orders = OrderService.get_recent_orders(limit=5)

    # Get chart data for last 30 days
    from datetime import datetime, timezone, timedelta
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=29)

    sales_by_date = OrderService.get_sales_by_date(date_from, date_to)
    chart_labels = []
    chart_data = []
    for row in sales_by_date:
        if row.date:
            if isinstance(row.date, str):
                parsed_date = date.fromisoformat(row.date)
            else:
                parsed_date = row.date

            chart_labels.append(parsed_date.strftime("%m/%d"))
        else:
            chart_labels.append("")

        chart_data.append(row.count)

    return render_template(
        "dashboard/index.html",
        order_stats=order_stats,
        product_stats=product_stats,
        inventory_stats=inventory_stats,
        recent_orders=recent_orders,
        chart_labels=chart_labels,
        chart_data=chart_data,
    )