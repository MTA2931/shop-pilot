"""Debug authentication."""
from app import create_app

app = create_app("testing")
with app.app_context():
    from app.models.administrator import Administrator
    admin = Administrator.query.filter_by(username="Admin").first()
    print("Admin found:", admin is not None)
    if admin:
        pw_ok = admin.check_password("admin123")
        print("Password check:", pw_ok)
        print("Must change:", admin.must_change_password)
        print("Is active:", admin.is_active)