"""Debug authentication flow."""
import os
import tempfile

# Create a temp database
db_fd, db_path = tempfile.mkstemp(suffix=".db")
os.close(db_fd)

# Override config
import config as config_module
config_module.TestingConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

print("TestingConfig.DEFAULT_ADMIN_USERNAME:", config_module.TestingConfig.DEFAULT_ADMIN_USERNAME)
print("TestingConfig.DEFAULT_ADMIN_PASSWORD:", config_module.TestingConfig.DEFAULT_ADMIN_PASSWORD)

from app import create_app
app = create_app("testing")

print("App config DEFAULT_ADMIN_USERNAME:", app.config.get("DEFAULT_ADMIN_USERNAME"))
print("App config DEFAULT_ADMIN_PASSWORD:", app.config.get("DEFAULT_ADMIN_PASSWORD"))

with app.app_context():
    from app.models.administrator import Administrator
    from app.extensions import db
    
    # List all admins
    all_admins = Administrator.query.all()
    print("All admins:", [(a.id, a.username, a.role) for a in all_admins])

# Cleanup
try:
    os.unlink(db_path)
except:
    pass