from ..app import db

tags = db.Table(
    "tag_links",
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id"), primary_key=True),
    info={"bind_key": "media"},
)


class FileKey(db.Model):
    __tablename__ = "file_keys"
    __bind_key__ = "media"

    enc_key = db.Column(db.String(), primary_key=True, nullable=False)
    iv = db.Column(db.String(16), nullable=False)


class Post(db.Model):
    __tablename__ = "posts"
    __bind_key__ = "media"

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    timestamp = db.Column(db.String())
    post = db.Column(db.String())
    media_files = db.Column(db.Integer)
    url = db.Column(db.String())
    url_label = db.Column(db.String())
    place_name = db.Column(db.String())
    address = db.Column(db.String())
    latitude = db.Column(db.String())
    longitude = db.Column(db.String())
    profile_update = db.Column(db.Boolean)
    tags = db.relationship("Tag", secondary=tags, lazy="subquery", backref=db.backref("pages", lazy=True))


class Media(db.Model):
    __tablename__ = "media"
    __bind_key__ = "media"

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    timestamp = db.Column(db.String())
    title = db.Column(db.String())
    description = db.Column(db.String())
    latitude = db.Column(db.String())
    longitude = db.Column(db.String())
    orientation = db.Column(db.Integer)
    filepath = db.Column(db.String(), index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    album_id = db.Column(db.Integer, db.ForeignKey("albums.id"))
    media_type = db.Column(db.String())
    thumbnail = db.Column(db.Integer)


class Album(db.Model):
    __tablename__ = "albums"
    __bind_key__ = "media"

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    last_modified = db.Column(db.String())
    name = db.Column(db.String())
    description = db.Column(db.String())
    total_files = db.Column(db.Integer)
    cover_photo_id = db.Column(db.Integer, db.ForeignKey("media.id"))


class Tag(db.Model):
    __tablename__ = "tags"
    __bind_key__ = "media"

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    tag = db.Column(db.String())
