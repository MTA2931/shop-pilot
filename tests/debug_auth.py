"""Debug authentication."""
from app import create_app

app = create_app("testing")
with app.app_context():
    from app.models.administrator import Administrator
    admin = Administrator.query.filter_by(username="Admin").first()
    print(f"Admin found: {admin is not None}")
    if admin:
        print(f"Password check: {admin.check_password('admin123')}")
        print(f"Must change: {admin.must_change_password}")
        print(f"Is active: {admin.is_active}")