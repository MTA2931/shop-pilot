"""Administrator management routes with RBAC."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.models.administrator import Administrator
from app.extensions import db

administrators_bp = Blueprint("administrators", __name__, url_prefix="/administrators")


def require_super_admin():
    """Helper to check super admin access."""
    if not current_user.is_super_admin():
        flash("دسترسی فقط برای سوپر ادمین‌ها مجاز است.", "danger")
        return False
    return True


@administrators_bp.route("/")
@login_required
def index():
    """List all administrators."""
    if not current_user.is_admin():
        flash("دسترسی مجاز نیست.", "danger")
        return redirect(url_for("dashboard.index"))

    admins = Administrator.query.order_by(Administrator.created_at.desc()).all()
    return render_template("administrators/index.html", admins=admins)

@administrators_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Create a new administrator (super admin only)."""
    if not require_super_admin():
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip() or None
        full_name = request.form.get("full_name", "").strip() or None
        role = request.form.get("role", "manager")
        password = request.form.get("password", "")
        is_active = request.form.get("is_active") == "on"

        if Administrator.query.filter_by(username=username).first():
            flash("نام کاربری قبلاً استفاده شده است.", "danger")
            return render_template("administrators/create.html")

        if email and Administrator.query.filter_by(email=email).first():
            flash("آدرس ایمیل قبلاً استفاده شده است.", "danger")
            return render_template("administrators/create.html")

        from app.services.auth_service import validate_password, PasswordValidationError
        try:
            validate_password(password, reject_default=False)
        except PasswordValidationError as e:
            flash(str(e), "danger")
            return render_template("administrators/create.html")

        admin = Administrator(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            is_active=is_active,
            must_change_password=True,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        from app.services.logging_service import log_activity
        log_activity(
            administrator_id=current_user.id,
            action="create_administrator",
            category="administrator",
            description=f"Administrator created: {username} ({role})",
            entity_type="administrator",
            entity_id=admin.id,
        )

        flash("ادمین با موفقیت ایجاد شد. در اولین ورود باید رمز عبور را تغییر دهد.", "success")
        return redirect(url_for("administrators.index"))

    return render_template("administrators/create.html")

@administrators_bp.route("/<int:admin_id>/edit", methods=["GET", "POST"])
@login_required
def edit(admin_id):
    """Edit an administrator (super admin only)."""
    if not require_super_admin():
        return redirect(url_for("dashboard.index"))

    admin = Administrator.query.get(admin_id)
    if not admin:
        flash("ادمین یافت نشد.", "danger")
        return redirect(url_for("administrators.index"))

    if request.method == "POST":
        admin.email = request.form.get("email", "").strip() or None
        admin.full_name = request.form.get("full_name", "").strip() or None
        admin.role = request.form.get("role", admin.role)
        admin.is_active = request.form.get("is_active") == "on"

        if admin.id == current_user.id and not admin.is_active:
            flash("نمی‌توانید حساب خود را غیرفعال کنید.", "danger")
            return render_template("administrators/edit.html", admin=admin)

        db.session.commit()

        from app.services.logging_service import log_activity
        log_activity(
            administrator_id=current_user.id,
            action="update_administrator",
            category="administrator",
            description=f"Administrator updated: {admin.username}",
            entity_type="administrator",
            entity_id=admin.id,
        )

        flash("ادمین با موفقیت به‌روزرسانی شد.", "success")
        return redirect(url_for("administrators.index"))

    return render_template("administrators/edit.html", admin=admin)


@administrators_bp.route("/<int:admin_id>/delete", methods=["POST"])
@login_required
def delete(admin_id):
    """Delete an administrator (super admin only)."""
    if not require_super_admin():
        return jsonify({"success": False, "message": "دسترسی مجاز نیست."}), 403

    admin = Administrator.query.get(admin_id)
    if not admin:
        return jsonify({"success": False, "message": "ادمین یافت نشد."}), 404

    from app.services.auth_service import admin_can_delete_or_deactivate
    allowed, reason = admin_can_delete_or_deactivate(admin, current_user)
    if not allowed:
        return jsonify({"success": False, "message": reason}), 403

    db.session.delete(admin)
    db.session.commit()

    from app.services.logging_service import log_activity
    log_activity(
        administrator_id=current_user.id,
        action="delete_administrator",
        category="administrator",
        description=f"Administrator deleted: {admin.username}",
        entity_type="administrator",
        entity_id=admin.id,
    )

    return jsonify({"success": True, "message": "ادمین با موفقیت حذف شد."})


@administrators_bp.route("/<int:admin_id>/toggle", methods=["POST"])
@login_required
def toggle(admin_id):
    """Activate/deactivate an administrator (super admin only)."""
    if not require_super_admin():
        return jsonify({"success": False, "message": "دسترسی مجاز نیست."}), 403

    admin = Administrator.query.get(admin_id)
    if not admin:
        return jsonify({"success": False, "message": "ادمین یافت نشد."}), 404

    if admin.id == current_user.id:
        return jsonify({"success": False, "message": "نمی‌توانید حساب خود را غیرفعال کنید."}), 403

    from app.services.auth_service import admin_can_delete_or_deactivate
    allowed, reason = admin_can_delete_or_deactivate(admin, current_user)
    if not allowed:
        return jsonify({"success": False, "message": reason}), 403

    admin.is_active = not admin.is_active
    db.session.commit()

    from app.services.logging_service import log_activity
    log_activity(
        administrator_id=current_user.id,
        action="toggle_administrator",
        category="administrator",
        description=f"Administrator {'activated' if admin.is_active else 'deactivated'}: {admin.username}",
        entity_type="administrator",
        entity_id=admin.id,
    )

    return jsonify({
        "success": True,
        "is_active": admin.is_active,
        "message": f"ادمین {'فعال' if admin.is_active else 'غیرفعال'} شد."
    })