from flask_user import UserMixin

from ..app import db


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
            collation="NOCASE",
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
            collation="NOCASE",
        ),
        nullable=False,
        server_default="",
    )
    last_name = db.Column(
        db.String(
            100,
            collation="NOCASE",
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


class UserKey(db.Model):
    __tablename__ = "user_key"
    encrypted_key = db.Column(
        db.String(),
        nullable=False,
        primary_key=True,
    )
    iv = db.Column(db.String(), nullable=False)


# class UserFileMetadata(db.Model):
#     __tablename__ = "user_file_metadata"


# class UserFile(db.Model):
#     filepath = db.Column(db.String(), nullable=False)
#     enc_file_key = db.Column(db.String(), nullable=False)
#     cid = db.Column(db.String(), nullable=False, primary_key=True)
