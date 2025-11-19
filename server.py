import os
import sys
from pathlib import Path

from flask import Flask

from models import db
from routes import register_routes
from utils import initialize_database

app = Flask(__name__, instance_relative_config=True)

# Ensure instance path exists and is writable
try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError as e:
    print(f"Warning: Could not create instance path {app.instance_path}: {e}", file=sys.stderr)
    # Fallback to /tmp if instance path fails
    app.instance_path = "/tmp/room_expenses_instance"
    os.makedirs(app.instance_path, exist_ok=True)

# Handle DATABASE_URL - Railway might provide postgres://, but we use SQLite
database_url = os.getenv("DATABASE_URL", "")
if database_url and database_url.startswith("postgres://"):
    # Railway provides PostgreSQL, but we'll use SQLite in instance folder
    # Convert postgres:// to postgresql:// if needed, or ignore and use SQLite
    print("Warning: DATABASE_URL is PostgreSQL, but using SQLite instead", file=sys.stderr)
    database_uri = f"sqlite:///{Path(app.instance_path) / 'room_expenses.db'}"
elif database_url and database_url.startswith("sqlite"):
    database_uri = database_url
else:
    # Default to SQLite in instance folder
    default_db_path = Path(app.instance_path) / "room_expenses.db"
    database_uri = f"sqlite:///{default_db_path}"

app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

db.init_app(app)

# Register all routes
register_routes(app)

# Initialize database
try:
    with app.app_context():
        initialize_database()
except Exception as e:
    print(f"Error initializing database: {e}", file=sys.stderr)
    # Don't fail completely - let the app start and handle errors per request


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
