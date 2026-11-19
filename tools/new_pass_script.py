import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.extensions import db
from app.models.administrator import Administrator

from getpass import getpass
from app.extensions import db
from app.models.administrator import Administrator
from app.services.auth_service import validate_password, PasswordValidationError

admin = Administrator.query.filter_by(username="Admin").first()

new_password = getpass("New temporary password: ")
confirm_password = getpass("Confirm password: ")

if new_password != confirm_password:
    print("Passwords do not match!")

else:
    try:
        validate_password(new_password, reject_default=True)

        admin.set_password(new_password)
        admin.must_change_password = True
        admin.failed_login_attempts = 0
        admin.locked_until = None

        db.session.commit()

        print("Password reset successfully!")

    except PasswordValidationError as error:
        print("Password validation failed:", error)