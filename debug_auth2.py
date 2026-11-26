"""Debug authentication flow."""
import os
import tempfile

# Create a temp database
db_fd, db_path = tempfile.mkstemp(suffix=".db")
os.close(db_fd)

# Override config
import config as config_module
config_module.TestingConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

from app import create_app
app = create_app("testing")

with app.app_context():
    from app.models.administrator import Administrator
    from app.extensions import db
    
    # Check count before
    count = Administrator.query.count()
    print("Administrator count before:", count)
    
    # Try ensure_default_administrator explicitly
    try:
        Administrator.ensure_default_administrator()
        print("ensure_default_administrator called successfully")
    except Exception as e:
        print(f"ensure_default_administrator failed: {e}")
    
    # Check after
    admin = Administrator.query.filter_by(username="Admin").first()
    print("Admin found:", admin is not None)
    if admin:
        print("Password check:", admin.check_password("admin123"))
        print("Must change:", admin.must_change_password)
        print("Is active:", admin.is_active)

# Cleanup
try:
    os.unlink(db_path)
except:
    pass