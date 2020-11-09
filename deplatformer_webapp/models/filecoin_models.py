from ..app import db
from .user_models import User


class Ffs(db.Model):
    """
    Define the attributes for a Powergate Filecoin FileSystem
    """

    id = db.Column(
        db.Integer(),
        primary_key=True,
    )
    ffs_id = db.Column(
        db.String(36),
        index=True,
    )
    token = db.Column(
        db.String(36),
        index=True,
    )
    creation_date = db.Column(db.DateTime())
    user_id = db.Column(
        db.Integer(),
        db.ForeignKey(User.id),
        nullable=False,
    )
    files = db.relationship(
        "Files",
        cascade="all,delete",
        backref="Ffs",
        lazy=True,
    )

    def __init__(
        self,
        ffs_id,
        token,
        creation_date,
        user_id,
    ):
        self.ffs_id = ffs_id
        self.token = token
        self.creation_date = creation_date
        self.user_id = user_id

    def __repr__(
        self,
    ):
        return self.ffs_id


class Files(db.Model):
    """
    Define the attributes for file uploads
    """

    id = db.Column(
        db.Integer(),
        primary_key=True,
    )
    file_path = db.Column(db.String(255))
    file_name = db.Column(
        db.String(255),
        index=True,
    )
    upload_date = db.Column(db.DateTime())
    file_size = db.Column(db.Integer())
    CID = db.Column(
        db.String(64),
        index=True,
    )
    platform = db.Column(
        db.String(255),
        index=True,
    )
    user_id = db.Column(
        db.Integer(),
        db.ForeignKey(User.id),
        nullable=False,
    )
    ffs_id = db.Column(
        db.Integer(),
        db.ForeignKey(Ffs.id),
        nullable=False,
    )

    def __init__(
        self,
        file_path,
        file_name,
        upload_date,
        file_size,
        CID,
        platform,
        user_id,
        ffs_id,
    ):
        self.file_path = file_path
        self.file_name = file_name
        self.upload_date = upload_date
        self.file_size = file_size
        self.CID = CID
        self.platform = platform
        self.user_id = user_id
        self.ffs_id = ffs_id

    def __repr__(
        self,
    ):
        return self.file_name


class Wallets(db.Model):
    """
    Define the attributes for wallets
    """

    id = db.Column(
        db.Integer(),
        primary_key=True,
    )
    created = db.Column(db.DateTime())
    address = db.Column(db.String(255))
    ffs = db.Column(db.String(255))
    user_id = db.Column(
        db.Integer(),
        db.ForeignKey(User.id),
        nullable=False,
    )

    def __init__(
        self,
        created,
        address,
        ffs,
        user_id,
    ):
        self.created = created
        self.address = address
        self.ffs = ffs
        self.user_id = user_id

    def __repr__(
        self,
    ):
        return self.address


class Logs(db.Model):
    """
    Define the attributes for log entries
    """

    id = db.Column(
        db.Integer(),
        primary_key=True,
    )
    timestamp = db.Column(db.DateTime())
    event = db.Column(db.String(255))
    user_id = db.Column(
        db.Integer(),
        db.ForeignKey(User.id),
        nullable=False,
    )

    def __init__(
        self,
        timestamp,
        event,
        user_id,
    ):
        self.timestamp = timestamp
        self.event = event
        self.user_id = user_id

    def __repr__(
        self,
    ):
        return self.event
