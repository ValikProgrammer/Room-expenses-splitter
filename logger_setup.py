import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(app):
    os.makedirs("logs", exist_ok=True)

    handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=5)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    handler.setFormatter(formatter)


    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Werkzeug
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.WARNING)
    werkzeug_logger.addHandler(handler)

    # SQLAlchemy 
    db_logger = logging.getLogger("sqlalchemy.engine")
    db_logger.setLevel(logging.INFO)
    db_handler = RotatingFileHandler("logs/db.log", maxBytes=1_000_000, backupCount=3)
    db_handler.setFormatter(formatter)
    db_logger.addHandler(db_handler)

    app.logger.info("Logging system initialized.")
    return app
