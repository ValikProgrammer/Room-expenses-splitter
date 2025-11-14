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
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

# initialize extensions and routes
db.init_app(app)
register_routes(app)

# create DB if not exists (runs safely inside app context)
with app.app_context():
    initialize_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
