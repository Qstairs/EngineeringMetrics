import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    logger.info("Starting Flask application initialization")
    app = Flask(__name__)

    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(basedir, 'app.db')
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    logger.info(f"Database URL configured: SQLite database at {os.path.join(basedir, 'app.db')}")

    # Initialize extensions
    try:
        logger.info("Initializing database")
        db.init_app(app)
        logger.info("Initializing login manager")
        login_manager.init_app(app)
        logger.info("Initializing migrations")
        migrate.init_app(app, db)
        login_manager.login_view = 'login'

        with app.app_context():
            # Import models here to avoid circular imports
            logger.info("Importing models")
            from models import User, Metric, DashboardPreference
            logger.info("Creating database tables")
            db.create_all()

            # Register routes
            logger.info("Registering routes")
            from routes import register_routes
            register_routes(app)

            logger.info("Application initialization completed successfully")
            return app
    except Exception as e:
        logger.error(f"Error during application initialization: {str(e)}")
        raise