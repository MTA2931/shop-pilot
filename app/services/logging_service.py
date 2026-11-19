"""Activity logging service - centralized audit trail."""

from flask import request
from flask_login import current_user

from app.extensions import db
from app.models.activity_log import ActivityLog


def log_activity(
    administrator_id=None,
    action=None,
    category="system",
    description=None,
    entity_type=None,
    entity_id=None,
):
    """Log an administrative activity.

    Never logs passwords, password hashes, session tokens, or other secrets.
    """
    if description is None:
        description = action

    # Get current user if not explicitly provided
    if administrator_id is None and current_user.is_authenticated:
        administrator_id = current_user.id

    ip_address = request.remote_addr if request else None
    user_agent = request.headers.get("User-Agent") if request else None

    log_entry = ActivityLog(
        administrator_id=administrator_id,
        action=action,
        category=category,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(log_entry)
    db.session.commit()