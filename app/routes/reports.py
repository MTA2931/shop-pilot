"""Reporting routes."""

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.services.report_service import ReportService
from datetime import datetime, timezone, timedelta

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    """Reports index with date range selection."""
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    # Default to last 30 days
    if not date_from:
        date_from = (datetime.now(timezone.utc) - timedelta(days=29)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    parsed_from = datetime.strptime(date_from, "%Y-%m-%d")
    parsed_to = datetime.strptime(date_to, "%Y-%m-%d")

    sales_data = ReportService.get_sales_report(parsed_from, parsed_to)
    order_data = ReportService.get_order_report(parsed_from, parsed_to)
    product_data = ReportService.get_product_report()
    inventory_data = ReportService.get_inventory_report()
    performance_data = ReportService.get_performance_report(parsed_from, parsed_to)
    movements_data = ReportService.get_inventory_movements_report(parsed_from, parsed_to)

    # Prepare chart data
    sales_labels = [row["date"] for row in sales_data]
    sales_counts = [row["order_count"] for row in sales_data]
    sales_amounts = [row["total_amount"] for row in sales_data]

    return render_template(
        "reports/index.html",
        date_from=date_from,
        date_to=date_to,
        sales_data=sales_data,
        order_data=order_data,
        product_data=product_data,
        inventory_data=inventory_data,
        performance_data=performance_data,
        movements_data=movements_data,
        sales_labels=sales_labels,
        sales_counts=sales_counts,
        sales_amounts=sales_amounts,
    )