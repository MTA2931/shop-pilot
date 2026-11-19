"""Authentication and password validation service."""

import re
from datetime import datetime, timezone, timedelta

from flask import current_app
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.administrator import Administrator
from app.services.logging_service import log_activity


class PasswordValidationError(Exception):
    """Raised when a password fails validation rules."""
    pass


COMMON_PASSWORD_PATTERNS = [
    r"^123456",
    r"^password",
    r"^qwerty",
    r"^abc123",
    r"^adminadmin",
    r"^admin",
    r"^admin123",
    r"^123456789",
    r"^12345678",
    r"^12345",
    r"^login",
    r"^iloveyou",
]


def validate_password(
    password: str,
    current_password: str = None,
    reject_default: bool = True,
) -> None:
    """Validate a password against all security rules.

    Raises PasswordValidationError with a descriptive message if invalid.
    """
    if not password:
        raise PasswordValidationError("رمز عبور نمی‌تواند خالی باشد.")

    min_len = current_app.config.get("PASSWORD_MIN_LENGTH", 10)
    if len(password) < min_len:
        raise PasswordValidationError(
            f"رمز عبور باید حداقل {min_len} کاراکتر باشد."
        )

    if current_app.config.get("PASSWORD_REQUIRE_UPPER", True):
        if not re.search(r"[A-Z]", password):
            raise PasswordValidationError(
                "رمز عبور باید حداقل شامل یک حرف بزرگ (A-Z) باشد."
            )

    if current_app.config.get("PASSWORD_REQUIRE_LOWER", True):
        if not re.search(r"[a-z]", password):
            raise PasswordValidationError(
                "رمز عبور باید حداقل شامل یک حرف کوچک (a-z) باشد."
            )

    if current_app.config.get("PASSWORD_REQUIRE_DIGIT", True):
        if not re.search(r"\d", password):
            raise PasswordValidationError(
                "رمز عبور باید حداقل شامل یک عدد باشد."
            )

    if current_app.config.get("PASSWORD_REQUIRE_SPECIAL", True):
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise PasswordValidationError(
                "رمز عبور باید حداقل شامل یک کاراکتر ویژه باشد."
            )

    # Reject commonly used passwords
    if current_app.config.get("PASSWORD_REJECT_COMMON", True):
        lower_pw = password.lower()
        for pattern in COMMON_PASSWORD_PATTERNS:
            if re.match(pattern, lower_pw):
                raise PasswordValidationError(
                    "این رمز عبور بسیار ساده است. لطفا رمز پیچیده‌تری انتخاب کنید."
                )

    # Reject the default password
    if reject_default and current_app.config.get("PASSWORD_REJECT_DEFAULT", True):
        default_pw = current_app.config.get("DEFAULT_ADMIN_PASSWORD", "admin123")
        if password == default_pw:
            raise PasswordValidationError(
                "نمی‌توانید از رمز عبور پیش‌فرض استفاده کنید."
            )

    # Reject password identical to current password
    if current_password and password == current_password:
        raise PasswordValidationError(
            "رمز عبور جدید نمی‌تواند همان رمز قبلی باشد."
        )


def authenticate_admin(username: str, password: str, ip_address: str = None, user_agent: str = None):
    """Authenticate an administrator by username and password.

    Returns (Administrator, error_message) tuple.
    """
    admin = Administrator.query.filter_by(username=username).first()

    if admin is None:
        log_activity(
            administrator_id=None,
            action="failed_login",
            category="authentication",
            description=f"Attempted login with non-existent username: {username}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return None, "نام کاربری یا رمز عبور اشتباه است."

    if not admin.is_active:
        log_activity(
            administrator_id=admin.id,
            action="failed_login_locked_account",
            category="authentication",
            description=f"Login attempt on deactivated account: {username}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return None, "حساب کاربری شما غیرفعال شده است. با پشتیبانی تماس بگیرید."

    if admin.is_locked():
        log_activity(
            administrator_id=admin.id,
            action="failed_login_account_locked",
            category="authentication",
            description=f"Login attempt on locked account: {username}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return None, "حساب کاربری شما به دلیل تلاش‌های مکرر موقتاً قفل شده است."

    if not admin.check_password(password):
        admin.record_failed_login()
        log_activity(
            administrator_id=admin.id,
            action="failed_login",
            category="authentication",
            description=f"Failed login attempt for: {username}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return None, "نام کاربری یا رمز عبور اشتباه است."

    # Successful login
    admin.reset_failed_logins()
    admin.current_login_at = datetime.now(timezone.utc)
    admin.current_login_ip = ip_address
    if admin.last_login_at is None:
        admin.last_login_at = admin.current_login_at
    db.session.commit()

    log_activity(
        administrator_id=admin.id,
        action="successful_login",
        category="authentication",
        description=f"Successful login: {username}",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return admin, None


def change_password(admin: Administrator, current_password: str, new_password: str) -> tuple:
    """Change an administrator's password after validation.

    Returns (success, error_message).
    """
    # Verify current password
    if not admin.check_password(current_password):
        return False, "رمز عبور فعلی اشتباه است."

    # Validate new password
    try:
        validate_password(
            new_password,
            current_password=current_password,
            reject_default=True,
        )
    except PasswordValidationError as e:
        return False, str(e)

    admin.set_password(new_password)
    admin.must_change_password = False
    db.session.commit()

    log_activity(
        administrator_id=admin.id,
        action="password_changed",
        category="authentication",
        description="Password changed successfully.",
    )

    return True, None


def admin_can_delete_or_deactivate(target_admin: Administrator, current_admin: Administrator) -> tuple:
    """Check if current_admin can delete or deactivate target_admin.

    Returns (allowed, reason).
    """
    if target_admin.id == current_admin.id:
        return False, "نمی‌توانید حساب خود را غیرفعال یا حذف کنید."

    if target_admin.is_super_admin():
        active_super_count = Administrator.count_active_super_admins()
        if active_super_count <= 1:
            return False, "نمی‌توان آخرین سوپر ادمین فعال را حذف یا غیرفعال کرد."

    if current_admin.is_super_admin():
        return True, None

    # Non-super admins cannot modify other admins at all
    return False, "فقط سوپر ادمین می‌تواند سایر ادمین‌ها را مدیریت کند."