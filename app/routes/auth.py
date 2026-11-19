"""Authentication routes: login, logout, change password."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.extensions import limiter
from app.services.auth_service import (
    authenticate_admin,
    change_password,
    validate_password,
    PasswordValidationError,
    admin_can_delete_or_deactivate,
)
from app.models.administrator import Administrator
from app.extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    """Handle administrator login with rate limiting."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent")

        admin, error = authenticate_admin(username, password, ip_address, user_agent)

        if error:
            flash(error, "danger")
            return render_template("auth/login.html")

        login_user(admin, remember=True)

        # Force password change for default administrator
        if admin.must_change_password:
            flash("لطفا رمز عبور خود را تغییر دهید.", "warning")
            return redirect(url_for("auth.change_password"))

        next_page = request.args.get("next")
        return redirect(next_page or url_for("dashboard.index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Logout the current administrator."""
    from app.services.logging_service import log_activity

    log_activity(
        administrator_id=current_user.id,
        action="logout",
        category="authentication",
        description=f"Administrator logged out: {current_user.username}",
    )
    logout_user()
    flash("با موفقیت خارج شدید.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Mandatory or voluntary password change."""
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            flash("رمز عبور جدید و تایید آن مطابقت ندارند.", "danger")
            return render_template("auth/change_password.html")

        try:
            validate_password(
                new_password,
                current_password=current_password,
                reject_default=True,
            )
        except PasswordValidationError as e:
            flash(str(e), "danger")
            return render_template("auth/change_password.html")

        success, error = change_password(current_user, current_password, new_password)
        if success:
            flash("رمز عبور با موفقیت تغییر کرد.", "success")
            if current_user.must_change_password:
                return redirect(url_for("dashboard.index"))
            return redirect(url_for("settings.profile"))
        else:
            flash(error, "danger")
            return render_template("auth/change_password.html")

    return render_template("auth/change_password.html")