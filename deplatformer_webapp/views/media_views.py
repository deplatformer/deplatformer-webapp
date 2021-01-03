import os
import sqlite3
from datetime import datetime

from flask import flash, render_template, request
from flask_user import current_user, login_required
from pygate_grpc.exceptions import GRPCNotAvailableException
from sqlalchemy import desc


from ..app import app, db
from ..helpers.facebook_helpers import clean_nametags, cut_hyperlinks, posts_to_db
from ..helpers.mediafile_helpers import create_user_dirs, save_upload_file
# from ..helpers.filecoin_helpers import push_dir_to_filecoin
from ..models import media
from ..models.user_models import UserDirectories


@app.route("/media")
@login_required
def media_view():
    day = datetime.now().strftime("%d")
    month_script = datetime.now().strftime("%b")
    directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()

    if directory is None:
        flash(
            "Facebook data not found.",
            "alert-danger",
        )
        return render_template(
            "media/media-view.html",
            breadcrumb="Media / View content",
            this_day=day,
            this_month=month_script,
        )

    # Sort albums so that Profile Pictures, Cover Photos, and Videos come first
    albums = media.Album.query.order_by(desc("last_modified")).all()
    #this is where the albums are disambiguated, by album name
    # todo: perform better unique disambiguation of albums, rather than just by name (currently can't support
    albums_dict = {album.name: album for album in albums}
    sorted_main_albums = [albums_dict[c] for c in ["Videos", "Cover Photos", "Profile Pictures"] if c in albums_dict]
    sorted_main_albums_names = [c for c in ["Videos", "Cover Photos", "Profile Pictures"] if c in albums_dict]
    sorted_other_albums = [albums_dict[d] for d in albums_dict if d not in sorted_main_albums_names]
    app.logger.debug(sorted_main_albums)
    return render_template(
        "facebook/facebook-view.html",
        breadcrumb="Facebook / View content",
        this_day=day,
        this_month=month_script,
        main_albums=sorted_main_albums,
        other_albums=sorted_other_albums,
    )


@app.route("/media/<media_id>")
@login_required
def media_folder_view(
    album_id,
):
    directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
    if directory is None:
        flash(
            "Facebook data not found.",
            "alert-danger",
        )
        return render_template(
            "facebook/facebook-view.html",
            breadcrumb="Facebook / View content ",
        )

    album = media.Album.query.filter_by(id=album_id)
    files = media.Media.query.filter((media.Media.album_id == album_id) & (media.Media.media_type.in_(["IMAGE", "VIDEO"]))).all()
    print(files)

    return render_template(
        "facebook/facebook-album.html",
        breadcrumb="Facebook / View content / Albums",
        files=files,
        album=album,
    )


@app.route("/facebook-manage")
@login_required
def facebook_manage():
    return render_template(
        "facebook/facebook-manage.html",
        breadcrumb="Facebook / Manage content",
    )
