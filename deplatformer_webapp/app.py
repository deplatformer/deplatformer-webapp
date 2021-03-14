import os
import sys

from flask import Flask
#needs migrate import for "upgrade" function
from flask_migrate import Migrate, migrate, upgrade
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserManager, login_required
from sqlalchemy import MetaData

from .config import app_config

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate()

from deplatformer_webapp.lib.tusfilter import TusFilter
from deplatformer_webapp.helpers.mediafile_helpers import handle_uploaded_file


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
    migrate.init_app(
        app,
        db,
        render_as_batch=True
    )

    if getattr(sys, 'frozen', False):
        with app.app_context():
            migrations_folder = os.path.join(sys._MEIPASS, 'migrations')
            print(migrations_folder)
            upgrade(directory=migrations_folder)
            app.config["cwd"] = sys._MEIPASS
    else:
        with app.app_context():
            cwd = os.path.abspath(os.path.dirname(__file__))
            print(os.path.join(cwd, "migrations"))
            upgrade(directory=os.path.join(cwd, "migrations"))
            app.config["cwd"] = cwd

    app.wsgi_app = TusFilter(
        app.wsgi_app,
        upload_path='/upload_resumable',
        tmp_dir=os.path.join(app.config["DATA_DIR"], "upload"),
        callback=upload_resumable_callback,
        flaskapp=app,
    )

    return app


app = create_app()

from .models import media, filecoin_models, user_models
from .views import media_views, facebook_views, views, upload_views

# Setup Flask-User and specify the User data-model
user_manager = UserManager(
    app,
    db,
    user_models.User,
)

