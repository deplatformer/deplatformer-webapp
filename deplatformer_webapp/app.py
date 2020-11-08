import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_user import UserManager

from .config import app_config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Factory function to create app instance"""
    env = os.getenv("FLASK_ENV", "dev")
    if env not in app_config:
        raise NameError(f"Config for environment '{env}' does not exist!")

    config_class = app_config[env]

    app = Flask(__name__, static_folder="static")
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)


    return app

def create_db(app):
    return SQLAlchemy(app)

app = create_app()

from .views import views, facebook_views, filecoin_views
from .models import user_models, filecoin_models

# Setup Flask-User and specify the User data-model
user_manager = UserManager(app, db, user_models.User)