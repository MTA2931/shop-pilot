"""Activity log routes."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.activity_log import ActivityLog
from app.extensions import db
from datetime import datetime as dt

logs_bp = Blueprint("logs", __name__, url_prefix="/logs")


@logs_bp.route("/")
@login_required
def index():
    """List activity logs with search, category filtering, date filtering, pagination."""
    if not current_user.is_admin():
        flash("دسترسی مجاز نیست.", "danger")
        return redirect(url_for("dashboard.index"))

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("search", "").strip() or None
    category_filter = request.args.get("category", "").strip() or None
    date_from = request.args.get("date_from", "").strip() or None
    date_to = request.args.get("date_to", "").strip() or None
    parsed_date_from = None
    parsed_date_to = None
    if date_from:
        try:
            parsed_date_from = dt.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            pass
    if date_to:
        try:
            parsed_date_to = dt.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            pass

    query = ActivityLog.query

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                ActivityLog.action.ilike(like),
                ActivityLog.description.ilike(like),
            )
        )

    if category_filter:
        query = query.filter_by(category=category_filter)

    if parsed_date_from:
        query = query.filter(ActivityLog.created_at >= parsed_date_from)
    if parsed_date_to:
        query = query.filter(ActivityLog.created_at <= parsed_date_to)

    pagination = query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    categories = [
        ("authentication", "احراز هویت"),
        ("administrator", "مدیریت ادمین‌ها"),
        ("order", "سفارش‌ها"),
        ("product", "محصولات"),
        ("inventory", "موجودی انبار"),
        ("system", "سیستم"),
        ("security", "امنیت"),
    ]

    return render_template(
        "logs/index.html",
        logs=pagination.items,
        pagination=pagination,
        search=search or "",
        category_filter=category_filter or "",
        date_from=date_from or "",
        date_to=date_to or "",
        categories=categories,
    )