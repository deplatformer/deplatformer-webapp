import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserManager

from .config import app_config

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    """Factory function to create app instance"""
    env = os.getenv(
        "FLASK_ENV",
        "local",
    )
    if env not in app_config:
        raise NameError(f"Config for environment '{env}' does not exist!")

    config_class = app_config[env]

    app = Flask(
        __name__,
        static_folder="static",
    )
    app.config.from_object(config_class)

    os.makedirs(app.config["DATA_DIR"],exist_ok=True)

    db.init_app(app)
    migrate.init_app(
        app,
        db,
    )

    return app


app = create_app()

from .models import filecoin_models, user_models
from .views import facebook_views, filecoin_views, views

# Setup Flask-User and specify the User data-model
user_manager = UserManager(
    app,
    db,
    user_models.User,
)
