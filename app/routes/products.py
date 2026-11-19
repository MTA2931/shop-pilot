"""Product management routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.services.product_service import ProductService
from app.models.product import Product

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/")
@login_required
def index():
    """List products with search, filtering, sorting, pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("search", "").strip() or None
    category_filter = request.args.get("category", "").strip() or None
    stock_filter = request.args.get("stock", "").strip() or None
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")

    pagination = ProductService.get_products(
        page=page,
        per_page=per_page,
        search=search,
        category_filter=category_filter,
        stock_filter=stock_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    categories = ProductService.get_categories()

    return render_template(
        "products/index.html",
        products=pagination.items,
        pagination=pagination,
        search=search or "",
        category_filter=category_filter or "",
        stock_filter=stock_filter or "",
        categories=categories,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@products_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Create a new product."""
    if request.method == "POST":
        data = {
            "name": request.form.get("name", "").strip(),
            "sku": request.form.get("sku", "").strip(),
            "description": request.form.get("description", "").strip(),
            "category": request.form.get("category", "").strip(),
            "price": request.form.get("price", 0),
            "stock_quantity": request.form.get("stock_quantity", 0),
            "min_stock_threshold": request.form.get("min_stock_threshold", 5),
        }

        product, error = ProductService.create_product(data, administrator_id=current_user.id)
        if error:
            flash(error, "danger")
            return render_template("products/create.html", product_data=data)

        flash("محصول با موفقیت ایجاد شد.", "success")
        return redirect(url_for("products.index"))

    return render_template("products/create.html")


@products_bp.route("/<int:product_id>")
@login_required
def detail(product_id):
    """View product details."""
    product = ProductService.get_product_by_id(product_id)
    if not product:
        flash("محصول یافت نشد.", "danger")
        return redirect(url_for("products.index"))
    return render_template("products/detail.html", product=product)


@products_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit(product_id):
    """Edit an existing product."""
    product = ProductService.get_product_by_id(product_id)
    if not product:
        flash("محصول یافت نشد.", "danger")
        return redirect(url_for("products.index"))

    if request.method == "POST":
        data = {
            "name": request.form.get("name", "").strip(),
            "sku": request.form.get("sku", "").strip(),
            "description": request.form.get("description", "").strip(),
            "category": request.form.get("category", "").strip(),
            "price": request.form.get("price", 0),
            "stock_quantity": request.form.get("stock_quantity", 0),
            "min_stock_threshold": request.form.get("min_stock_threshold", 5),
        }

        product, error = ProductService.update_product(product, data, administrator_id=current_user.id)
        if error:
            flash(error, "danger")
            return render_template("products/edit.html", product=product, product_data=data)

        flash("محصول با موفقیت به‌روزرسانی شد.", "success")
        return redirect(url_for("products.index"))

    return render_template("products/edit.html", product=product)


@products_bp.route("/<int:product_id>/delete", methods=["POST"])
@login_required
def delete(product_id):
    """Delete a product."""
    product = ProductService.get_product_by_id(product_id)
    if not product:
        flash("محصول یافت نشد.", "danger")
        return redirect(url_for("products.index"))

    ProductService.delete_product(product, administrator_id=current_user.id)
    flash("محصول با موفقیت حذف شد.", "success")
    return redirect(url_for("products.index"))