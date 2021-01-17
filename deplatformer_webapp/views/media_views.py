import os
import sqlite3
from datetime import datetime

from flask import flash, render_template, request, redirect, url_for
from flask_user import current_user, login_required
from pygate_grpc.exceptions import GRPCNotAvailableException
from sqlalchemy import desc, select

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
            "Media not found.",
            "alert-danger",
        )
        return render_template(
            "uploader/uploader.html",
            breadcrumb="All Media / Upload",
            user=current_user
        )

    # Sort albums so that Profile Pictures, Cover Photos, and Videos come first
    toplevel = media.Media.query.filter_by(user_id=current_user.id, parent_id=None,
                                           container_type="ALBUM",
                                           ).order_by(desc("last_modified")).first()

    source_albums = media.Media.query.filter_by(user_id=current_user.id, parent_id=toplevel.id,
                                                container_type="ALBUM",
                                                ).order_by(desc("last_modified")).all()

    # for every album with a parent in source_albums
    source_albums_ids = [album.id for album in source_albums]
    second_level_albums = media.Media.query.filter(
        (media.Media.user_id == current_user.id) & (media.Media.container_type == "ALBUM") & (
            media.Media.parent_id.in_(source_albums_ids))).all()

    # second_level_album_ids = [album.id for album in source_albums]

    second_level_album_objects = []
    for item in second_level_albums:
        container = media.Media.query.filter_by(user_id=current_user.id, parent_id=item.id,
                                                container_type="CONTAINER",
                                                ).order_by(desc("last_modified")).first()
        # cover_photo = media.Media.query.filter_by(user_id=current_user.id, parent_id=container.id,
        #                             container_type="CLEAR_THUMBNAIL",
        #                             ).order_by(desc("last_modified")).first()
        album_object = {
            "album": item,
            "cover_photo_id": container.id
        }
        second_level_album_objects.append(album_object)

    # this is where the albums are disambiguated, by album name
    # todo: perform better unique disambiguation of albums, rather than just by name (currently can't support
    albums_dict = {album["album"].name: album for album in second_level_album_objects}
    sorted_main_albums = [albums_dict[c] for c in ["Videos", "Cover Photos", "Profile Pictures"] if c in albums_dict]
    sorted_main_albums_names = [c for c in ["Videos", "Cover Photos", "Profile Pictures"] if c in albums_dict]
    sorted_other_albums = [albums_dict[d] for d in albums_dict if d not in sorted_main_albums_names]
    app.logger.debug(sorted_main_albums)
    return render_template(
        "media/media-view.html",
        breadcrumb="Media / View Albums",
        this_day=day,
        this_month=month_script,
        main_albums=sorted_main_albums,
        other_albums=sorted_other_albums,
    )


@app.route("/media/<album_id>")
@login_required
def media_folder_view(
        album_id,
):
    # directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
    # if directory is None:
    #     flash(
    #         "Facebook data not found.",
    #         "alert-danger",
    #     )
    #     return render_template(
    #         "facebook/facebook-view.html",
    #         breadcrumb="Facebook / View content ",
    #     )
    args = request.args

    if "platform_name" in args:
        platform_name = args["platform_name"]
    else:
        platform_name = None

    album = media.Media.query.filter_by(user_id=current_user.id, id=album_id).first()
    containers = media.Media.query.filter((media.Media.parent_id == album_id)
                                          & (media.Media.container_type.in_(["CONTAINER", "ALBUM"]))
                                          # & (media.Media.media_type.in_(["IMAGE", "VIDEO"]))
                                          ).all()
    # print(files)

    album_objects = []
    for item in containers:
        # container = media.Media.query.filter_by(user_id=current_user.id, parent_id=item.id,
        #                             container_type="CONTAINER",
        #                             ).order_by(desc("last_modified")).first()
        if item.container_type == "ALBUM":
            first_image = media.Media.query.filter_by(user_id=current_user.id, parent_id=item.id,
                                                    container_type="CONTAINER",
                                                    ).order_by(desc("last_modified")).first()

            # thumbnail = media.Media.query.filter_by(user_id=current_user.id, parent_id=first_image.id,
            #                                         container_type="CLEAR_THUMBNAIL",
            #                                         ).order_by(desc("last_modified")).first()

            album_object = {
                "album": item,
                "container": first_image
            }
        else:
            album_object = {
                "container": item,
            }

        album_objects.append(album_object)

    return render_template(
        "media/media-album.html",
        breadcrumb="Media / View content / Albums",
        platform_name=platform_name,
        containers=album_objects,
        album=album,
    )


@app.route("/media/platform/<platform_name>")
@login_required
def media_platform_view(
        platform_name,
):

    # Sort albums so that Profile Pictures, Cover Photos, and Videos come first
    toplevel = media.Media.query.filter_by(user_id=current_user.id, parent_id=None,
                                           container_type="ALBUM",
                                           ).order_by(desc("last_modified")).first()

    platform_album = media.Media.query.filter_by(user_id=current_user.id, parent_id=toplevel.id,
                                                container_type="ALBUM",
                                                source=platform_name,
                                                ).order_by(desc("id")).first()

    return redirect(url_for('media_folder_view', album_id=platform_album.id, platform_name=platform_name))