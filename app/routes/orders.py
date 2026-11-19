"""Order management routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.services.order_service import OrderService
from app.models.order import Order

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.route("/")
@login_required
def index():
    """List orders with search, filtering, sorting, pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("search", "").strip() or None
    status_filter = request.args.get("status", "").strip() or None
    date_from = request.args.get("date_from", "").strip() or None
    date_to = request.args.get("date_to", "").strip() or None
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")

    # Parse dates
    from datetime import datetime
    parsed_date_from = None
    parsed_date_to = None
    if date_from:
        try:
            parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            pass
    if date_to:
        try:
            parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            pass

    pagination = OrderService.get_orders(
        page=page,
        per_page=per_page,
        search=search,
        status_filter=status_filter,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return render_template(
        "orders/index.html",
        orders=pagination.items,
        pagination=pagination,
        search=search or "",
        status_filter=status_filter or "",
        date_from=date_from or "",
        date_to=date_to or "",
        sort_by=sort_by,
        sort_order=sort_order,
    )


@orders_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Create a new order."""
    if request.method == "POST":
        data = {
            "customer_name": request.form.get("customer_name", "").strip(),
            "customer_phone": request.form.get("customer_phone", "").strip(),
            "customer_address": request.form.get("customer_address", "").strip(),
            "description": request.form.get("description", "").strip(),
            "total_amount": request.form.get("total_amount", 0),
            "status": request.form.get("status", "pending"),
            "channel": request.form.get("channel", "website"),
        }

        order, error = OrderService.create_order(data, administrator_id=current_user.id)
        if error:
            flash(error, "danger")
            return render_template("orders/create.html", order_data=data)

        flash("سفارش با موفقیت ایجاد شد.", "success")
        return redirect(url_for("orders.index"))

    return render_template("orders/create.html")


@orders_bp.route("/<int:order_id>")
@login_required
def detail(order_id):
    """View order details."""
    order = OrderService.get_order_by_id(order_id)
    if not order:
        flash("سفارش یافت نشد.", "danger")
        return redirect(url_for("orders.index"))
    return render_template("orders/detail.html", order=order)


@orders_bp.route("/<int:order_id>/edit", methods=["GET", "POST"])
@login_required
def edit(order_id):
    """Edit an existing order."""
    order = OrderService.get_order_by_id(order_id)
    if not order:
        flash("سفارش یافت نشد.", "danger")
        return redirect(url_for("orders.index"))

    if request.method == "POST":
        data = {
            "customer_name": request.form.get("customer_name", "").strip(),
            "customer_phone": request.form.get("customer_phone", "").strip(),
            "customer_address": request.form.get("customer_address", "").strip(),
            "description": request.form.get("description", "").strip(),
            "total_amount": request.form.get("total_amount", 0),
            "status": request.form.get("status", order.status),
            "channel": request.form.get("channel", "website"),
        }

        order, error = OrderService.update_order(order, data, administrator_id=current_user.id)
        if error:
            flash(error, "danger")
            return render_template("orders/edit.html", order=order, order_data=data)

        flash("سفارش با موفقیت به‌روزرسانی شد.", "success")
        return redirect(url_for("orders.index"))

    return render_template("orders/edit.html", order=order)


@orders_bp.route("/<int:order_id>/delete", methods=["POST"])
@login_required
def delete(order_id):
    """Delete an order."""
    order = OrderService.get_order_by_id(order_id)
    if not order:
        flash("سفارش یافت نشد.", "danger")
        return redirect(url_for("orders.index"))

    OrderService.delete_order(order, administrator_id=current_user.id)
    flash("سفارش با موفقیت حذف شد.", "success")
    return redirect(url_for("orders.index"))


@orders_bp.route("/<int:order_id>/status", methods=["POST"])
@login_required
def change_status(order_id):
    """Change order status via AJAX or form."""
    order = OrderService.get_order_by_id(order_id)
    if not order:
        return jsonify({"success": False, "message": "سفارش یافت نشد."}), 404

    new_status = request.form.get("status", "").strip()
    order, error = OrderService.change_status(order, new_status, administrator_id=current_user.id)
    if error:
        return jsonify({"success": False, "message": error}), 400

    return jsonify({"success": True, "message": "وضعیت سفارش به‌روزرسانی شد."})