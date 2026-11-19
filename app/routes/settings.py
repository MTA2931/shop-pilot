"""Account settings routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.services.auth_service import change_password, validate_password, PasswordValidationError

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Administrator profile settings."""
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", "").strip() or None
        current_user.email = request.form.get("email", "").strip() or None

        from app.extensions import db
        from app.models.administrator import Administrator

        email = current_user.email
        if email and Administrator.query.filter(
            Administrator.email == email,
            Administrator.id != current_user.id
        ).first():
            flash("آدرس ایمیل قبلاً استفاده شده است.", "danger")
            return render_template("settings/profile.html")

        db.session.commit()
        flash("پروفایل با موفقیت به‌روزرسانی شد.", "success")
        return redirect(url_for("settings.profile"))

    return render_template("settings/profile.html")


@settings_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password_settings():
    """Change password from settings page."""
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            flash("رمز عبور جدید و تایید آن مطابقت ندارند.", "danger")
            return render_template("settings/change_password.html")

        try:
            validate_password(
                new_password,
                current_password=current_password,
                reject_default=True,
            )
        except PasswordValidationError as e:
            flash(str(e), "danger")
            return render_template("settings/change_password.html")

        success, error = change_password(current_user, current_password, new_password)
        if success:
            flash("رمز عبور با موفقیت تغییر کرد.", "success")
            return redirect(url_for("settings.profile"))
        else:
            flash(error, "danger")
            return render_template("settings/change_password.html")

    return render_template("settings/change_password.html")


@settings_bp.route("/security")
@login_required
def security():
    """Account security information."""
    return render_template("settings/security.html")


@settings_bp.route("/logout")
@login_required
def logout():
    """Logout from settings."""
    from flask import redirect, url_for
    from app.services.logging_service import log_activity

    log_activity(
        administrator_id=current_user.id,
        action="logout",
        category="authentication",
        description=f"Administrator logged out: {current_user.username}",
    )
    from flask_login import logout_user
    logout_user()
    flash("با موفقیت خارج شدید.", "info")
    return redirect(url_for("auth.login"))