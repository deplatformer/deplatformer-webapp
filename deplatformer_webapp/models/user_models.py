from flask_user import UserMixin

from ..app import db
from ..helpers.db import get_collation_by_engine


class User(
    db.Model,
    UserMixin,
):
    __tablename__ = "users"
    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    active = db.Column(
        "is_active",
        db.Boolean(),
        nullable=False,
        server_default="1",
    )

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = db.Column(
        db.String(
            100,
            collation=get_collation_by_engine(),
        ),
        nullable=False,
        unique=True,
    )
    password = db.Column(
        db.String(255),
        nullable=False,
        server_default="",
    )
    email_confirmed_at = db.Column(db.DateTime())

    # User information
    first_name = db.Column(
        db.String(
            100,
            collation=get_collation_by_engine(),
        ),
        nullable=False,
        server_default="",
    )
    last_name = db.Column(
        db.String(
            100,
            collation=get_collation_by_engine(),
        ),
        nullable=False,
        server_default="",
    )


class UserDirectories(db.Model):
    __tablename__ = "user_directories"
    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    platform = db.Column(
        db.String(),
        nullable=False,
    )
    directory = db.Column(
        db.String(),
        nullable=False,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )
