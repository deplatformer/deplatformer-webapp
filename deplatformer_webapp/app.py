import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserManager, login_required

from .config import app_config

db = SQLAlchemy()
migrate = Migrate()

from .lib.tusfilter import TusFilter
from .helpers.media_helpers import handle_uploaded_file


def upload_resumable_callback(app, tmpfileid, user):
    # do something else
    # set current app
    # set current config

    # app.app_context().push()
    # with app.app_context():
    # db.init_app(flaskapp)
    #
    # env = os.getenv(
    #     "FLASK_ENV",
    #     "local",
    # )
    # if env not in app_config:
    #     raise NameError(f"Config for environment '{env}' does not exist!")
    #
    # config_class = app_config[env]
    # app.config.from_object(config_class)
    #
    # db.init_app(app)
    handle_uploaded_file(app, tmpfileid, user)
    return 'End of upload'


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

    os.makedirs(app.config["DATA_DIR"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(
        app,
        db,
    )

    app.wsgi_app = TusFilter(
        app.wsgi_app,
        upload_path='/upload_resumable',
        tmp_dir='tmp', # todo: config this
        callback=upload_resumable_callback,
        flaskapp=app,
    )

    return app


app = create_app()

from .models import media, filecoin_models, user_models
from .views import facebook_views, filecoin_views, views, upload_views

# Setup Flask-User and specify the User data-model
user_manager = UserManager(
    app,
    db,
    user_models.User,
)

