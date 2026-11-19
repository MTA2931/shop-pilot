"""Inventory management routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.services.inventory_service import InventoryService
from app.models.product import Product
from app.models.inventory import InventoryItem, InventoryMovement

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@inventory_bp.route("/")
@login_required
def index():
    """Inventory overview and item list."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("search", "").strip() or None
    stock_filter = request.args.get("stock", "").strip() or None
    sort_by = request.args.get("sort_by", "name")
    sort_order = request.args.get("sort_order", "asc")

    stats = InventoryService.get_stats()
    pagination = InventoryService.get_inventory_items(
        page=page,
        per_page=per_page,
        search=search,
        stock_filter=stock_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return render_template(
        "inventory/index.html",
        stats=stats,
        items=pagination.items,
        pagination=pagination,
        search=search or "",
        stock_filter=stock_filter or "",
        sort_by=sort_by,
        sort_order=sort_order,
    )


@inventory_bp.route("/movements")
@login_required
def movements():
    """Stock movement history."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("search", "").strip() or None
    movement_type = request.args.get("type", "").strip() or None
    date_from = request.args.get("date_from", "").strip() or None
    date_to = request.args.get("date_to", "").strip() or None

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

    pagination = InventoryService.get_movements(
        page=page,
        per_page=per_page,
        search=search,
        movement_type=movement_type,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
    )

    return render_template(
        "inventory/movements.html",
        movements=pagination.items,
        pagination=pagination,
        search=search or "",
        movement_type=movement_type or "",
        date_from=date_from or "",
        date_to=date_to or "",
    )


@inventory_bp.route("/adjust", methods=["POST"])
@login_required
def adjust():
    """Adjust stock for a product."""
    product_id = request.form.get("product_id", type=int)
    quantity_change = request.form.get("quantity_change", type=int)
    movement_type = request.form.get("movement_type", "adjustment")
    reason = request.form.get("reason", "").strip()
    notes = request.form.get("notes", "").strip()

    if not product_id or quantity_change is None:
        flash("داده‌های نامعتبر.", "danger")
        return redirect(url_for("inventory.index"))

    product = Product.query.get(product_id)
    if not product:
        flash("محصول یافت نشد.", "danger")
        return redirect(url_for("inventory.index"))

    inventory_item, error = InventoryService.adjust_stock(
        product_id=product_id,
        quantity_change=quantity_change,
        movement_type=movement_type,
        reason=reason or "تغییر موجودی",
        notes=notes,
        administrator_id=current_user.id,
    )
    if error:
        flash(error, "danger")
    else:
        flash(f"موجودی محصول {product.name} با موفقیت به‌روزرسانی شد.", "success")

    return redirect(url_for("inventory.index"))