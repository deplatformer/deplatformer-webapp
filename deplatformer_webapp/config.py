"""
Configuration for Deplatformer WebApp
"""
import logging
import os
import platform


class Config:
    """Parent configuration class."""

    ENV = os.getenv(
        "FLASK_ENV",
        "local",
    )
    DEBUG = os.getenv(
        "FLASK_DEBUG",
        True,
    )

    APPLICATION_ROOT = "/"

    APP_LOG_LEVEL = logging.INFO
    LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(filename)s:%(lineno)d " "%(message)s"

    

    # Flask settings
    SECRET_KEY = "3d488586-35ec-4706-ab35-cb46e59f11b6"

    # Powergate address
    POWERGATE_ADDRESS = os.getenv(
        "POWERGATE_ADDR",
        "127.0.0.1:5002",
    )

    # Directories to store Deplatformer's data
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.getenv(
        "DATA_DIR",
        os.path.join(os.getenv("APPDATA"), "Deplatformer") if platform.system() == "Windows" else os.path.expanduser("~/.deplatformer")
    )
    USER_DATA_DIR = os.path.join(DATA_DIR, "_user_data")

    # Flask-SQLAlchemy settings
    # File-based SQL database
    SQLITE_DB = os.path.join(DATA_DIR, "deplatformr.sqlite")
    SQLALCHEMY_DATABASE_URI = f"sqlite:////{SQLITE_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    IPFS_STAGING_DIR = os.path.join(DATA_DIR, ".ipfs-staging")
    IPFS_DATA_DIR = os.path.join(DATA_DIR, ".ipfs-data")
    IPFS_URI = os.getenv(
        "IPFS_URI",
        "/dns/localhost/tcp/5001/http",
    )

    # Flask-User settings
    # See https://flask-user.readthedocs.io/en/latest/configuring_settings.html
    # Shown in and email templates and page footers
    USER_APP_NAME = "Deplatformr - Prototype"
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_CONFIRM_EMAIL = False
    USER_REQUIRE_RETYPE_PASSWORD = True
    USER_ENABLE_CHANGE_USERNAME = False
    USER_ENABLE_CHANGE_PASSWORD = True
    USER_ENABLE_REMEMBER_ME = False
    USER_AUTO_LOGIN = True
    USER_AUTO_LOGIN_AFTER_CONFIRM = True
    USER_AUTO_LOGIN_AFTER_REGISTER = True
    USER_AUTO_LOGIN_AFTER_RESET_PASSWORD = True
    USER_AUTO_LOGIN_AT_LOGIN = True
    USER_AFTER_LOGOUT_ENDPOINT = "user.login"


class LocalConfig(Config):
    ENV = os.getenv(
        "FLASK_ENV",
        "local",
    )
    DEBUG = os.getenv(
        "FLASK_DEBUG",
        True,
    )


class DevelopmentConfig(Config):
    ENV = os.getenv(
        "FLASK_ENV",
        "dev",
    )
    DEBUG = os.getenv(
        "FLASK_DEBUG",
        True,
    )


app_config = {
    # "test": TestingConfig,
    "local": LocalConfig,
    "dev": DevelopmentConfig,
    # "staging": StagingConfig,
    # "prod": ProductionConfig,
}
