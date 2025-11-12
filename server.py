import os
from pathlib import Path

from flask import Flask

from models import db
from routes import register_routes
from utils import initialize_database

app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)

default_db_path = Path(app.instance_path) / "room_expenses.db"
database_uri = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")

app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev-secret-key"  # Used for flash messages; replace in production.

db.init_app(app)

# Register all routes
register_routes(app)

# Initialize database
with app.app_context():
    initialize_database()


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
