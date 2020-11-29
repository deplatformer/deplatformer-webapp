import os
import sys

from flask import Flask
#needs migrate import for "upgrade" function
from flask_migrate import Migrate, migrate, upgrade
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserManager

from .config import app_config

db = SQLAlchemy()
flask_migrate = Migrate()


def create_app():
    """Factory function to create app instance"""
    env = os.getenv(
        "FLASK_ENV",
        "production",
    )
    if env not in app_config:
        raise NameError(f"Config for environment '{env}' does not exist!")

    print(env)

    config_class = app_config[env]

    if getattr(sys, 'frozen', False):
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'static')
        app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    else:
        app = Flask(
            __name__,
            # template_folder="templates",
            static_folder="static",
        )
    app.config.from_object(config_class)

    os.makedirs(app.config["DATA_DIR"], exist_ok=True)

    db.init_app(app)
    flask_migrate.init_app(
        app,
        db,
    )
    if getattr(sys, 'frozen', False):
        with app.app_context():
            migrations_folder = os.path.join(sys._MEIPASS, 'migrations')
            print(migrations_folder)
            upgrade(directory=migrations_folder)
    else:
        with app.app_context():
            cwd = os.path.abspath(os.path.dirname(__file__))
            print(os.path.join(cwd, "migrations"))
            upgrade(directory=os.path.join(cwd, "migrations"))

    return app


app = create_app()

from .models import facebook, filecoin_models, user_models
from .views import facebook_views, filecoin_views, views

# Setup Flask-User and specify the User data-model
user_manager = UserManager(
    app,
    db,
    user_models.User,
)
