import os
from pathlib import Path

from flask import Flask

from models import db
from routes import register_routes
from utils import initialize_database

app = Flask(__name__, instance_relative_config=True)


import logging
from logger_setup import setup_logger
# logging.basicConfig(level=logging.INFO)
app = setup_logger(app)
app.logger.setLevel(logging.INFO)


try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError as e:
    app.logger.warning(f"Could not create instance path {app.instance_path}: {e}")
    # Fallback to /tmp if instance path fails
    app.instance_path = "/tmp/room_expenses_instance"
    os.makedirs(app.instance_path, exist_ok=True)


database_url = os.getenv("DATABASE_URL", "")
if database_url and database_url.startswith("postgres"):
    # Use PostgreSQL if provided via DATABASE_URL
    database_uri = database_url.replace("postgres://", "postgresql://", 1)
    app.logger.info("Using PostgreSQL database from DATABASE_URL")
elif database_url and database_url.startswith("sqlite"):
    database_uri = database_url
    app.logger.info("Using SQLite database from DATABASE_URL")
else:
    # Default to SQLite in instance folder
    default_db_path = Path(app.instance_path) / "room_expenses.db"
    database_uri = f"sqlite:///{default_db_path}"
    app.logger.info(f"Using default SQLite database at {default_db_path}")

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
        app.logger.info("Database initialized successfully")
except Exception as e:
    app.logger.error(f"Error initializing database: {e}", exc_info=True)
    # Don't fail completely - let the app start and handle errors per request


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
