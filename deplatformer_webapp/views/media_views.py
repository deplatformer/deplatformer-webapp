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
def media_album_view(
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
    if album is None:
        flash(
            "Media not found.",
            "alert-danger",
        )
        return render_template(
            "media/media-view.html",
            breadcrumb="All Media / Upload",
            user=current_user
        )

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
        "uploader/album_uploader.html",
        breadcrumb="Media / View content / Albums",
        platform_name=platform_name,
        containers=album_objects,
        album=album,
        user=current_user
    )


@app.route("/media/album/create", methods=['POST'])
@login_required
def media_album_create(
):

    # with sqlite3.connect(app.config["MEDIA_SQLITE_DB"]) as db:
    args = request.form

    if "album_id" in args:
        album_id = args["album_id"]
    else:
        top_node = media.Media.query.filter_by(user_id=current_user.id, parent_id=None, container_type="ALBUM").first()
        if top_node is None:
            top_node = media.Media(
                user_id=current_user.id,
                name="Top",
                description="Media",
                container_type="ALBUM",
                parent_id=None,
                source="media",
            )
            db.session.add(top_node)
            db.session.commit()
        album_id = top_node.id

    if "album_name" in args:
        album_name = args["album_name"]
    else:
        album_name = None
        # todo: Error on no album name

    if "album_description" in args:
        album_description = args["album_description"]
    else:
        album_description = None

    if "source" in args:
        source = args["source"]
    else:
        source = "media"

    album = media.Media.query.filter_by(user_id=current_user.id, id=album_id, container_type="ALBUM").first()
    # containers = media.Media.query.filter((media.Media.parent_id == album_id)
    #                                       & (media.Media.container_type.in_(["CONTAINER", "ALBUM"]))
    #                                       # & (media.Media.media_type.in_(["IMAGE", "VIDEO"]))
    #                                       ).all()
    # print(files)


    # unix_time = album_contents.get("last_modified_timestamp", None)
    # last_modified = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S") if unix_time else None
    # description = album_contents.get("description", None)
    cover_photo = None  # get Media file id to use as foreign key

    new_album = media.Media.query.filter_by(user_id=current_user.id, parent_id=album.id,
                                  container_type="ALBUM", source=source,
                                  name=album_name).first()
    if new_album is None:
        # Save new album in db
        new_album = media.Media(
            user_id=current_user.id,
            parent_id=album.id,
            name=album_name,
            description=album_description,
            last_modified=datetime.now(),
            # cover_photo_id=cover_photo,
            source=source,
            container_type="ALBUM",
        )
        db.session.add(new_album)
        db.session.commit()
    else:
        # new album is not none
        # return a toast saying so
        print("Album exists")

    # return the new album in the album view
    return redirect(url_for('media_album_view', album_id=new_album.id, platform_name=source))



@app.route("/media/album/delete", methods=['POST'])
@login_required
def media_album_delete(
):

    # with sqlite3.connect(app.config["MEDIA_SQLITE_DB"]) as db:
    args = request.form

    if "album_id" in args:
        album_id = args["album_id"]
    else:
        # todo: throw error
        return redirect(url_for('media_album_view', album_id=top_node.id, ))

    # todo: delete all media also

    album = media.Media.query.filter_by(user_id=current_user.id, id=album_id, container_type="ALBUM").first()

    if album is not None:
        db.session.delete(album)
        db.session.commit()
        parent_id = album.parent_id
    else:
        # new album is not none
        # return a toast saying so
        print("Album doesn't exist")
        top_node = media.Media.query.filter_by(user_id=current_user.id, parent_id=None, container_type="ALBUM").first()
        parent_id = top_node.id

    # return the new album in the album view

    flash(
        "Album deleted.",
        "alert-info",
    )
    return redirect(url_for('media_album_view', album_id=parent_id))


@app.route("/media/platform/<platform_name>")
@login_required
def media_platform_view(
        platform_name,
):

    # Sort albums so that Profile Pictures, Cover Photos, and Videos come first
    toplevel = media.Media.query.filter_by(user_id=current_user.id, parent_id=None,
                                           container_type="ALBUM",
                                           ).order_by(desc("last_modified")).first()

    # reroute user to deplatform instructions if they have not yet uploaded
    # content
    if toplevel is None:
        return redirect (url_for('facebook_deplatform'))

    platform_album = media.Media.query.filter_by(user_id=current_user.id, parent_id=toplevel.id,
                                                container_type="ALBUM",
                                                source=platform_name,
                                                ).order_by(desc("id")).first()

    return redirect(url_for('media_album_view', album_id=platform_album.id, platform_name=platform_name))
