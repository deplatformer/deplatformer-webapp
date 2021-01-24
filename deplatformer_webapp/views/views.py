import os
import sqlite3

from flask import render_template, send_from_directory
from flask_user import current_user, login_required

from ..app import app, db
from ..crypto import create_user_key_if_not_exists
from ..helpers.media_helpers import create_thumbnail
from ..helpers.mediafile_helpers import create_user_dirs, get_user_dir
from ..models import media
from ..models.user_models import UserDirectories


@app.route("/")
@login_required
def homepage():
    create_user_key_if_not_exists(current_user.username, current_user.password, db)

    return render_template(
        "homepage.html",
        breadcrumb="Home",
    )

@app.route(
    "/userfile/<file_id>",
    methods=["GET"],
)
@login_required
def userfile(
    file_id,
):
    if file_id is None or file_id == 'None':
        return "File not found." #TODO: how to make 404?

    # directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
    # if directory is None:
    #     return "File not found."
    # todo: search for 2nd level directories

    # app.logger.debug("file_id: %s" % file_id)

    media_file = media.Media.query.filter_by(user_id=current_user.id, parent_id=file_id, container_type="CLEAR").first()

    if media_file is None:
        return "File not found."
    else:
        source = media_file.source
        directory_object = UserDirectories.query.filter_by(user_id=current_user.id, platform=source).first()
        if directory_object is None:
            directory = get_user_dir(current_user, app.config["USER_DATA_DIR"], source)
        else:
            directory = directory_object.directory

    filepath = media_file.filepath
    # media_type = media_file.media_type

    # filepath = None
    # if platform == "facebook":
    #     filepath = file.filepath

    # TODO: Determine file type from DB

    if filepath is None or directory is None:
        return "File not found."

    split = os.path.split(filepath)
    filename = split[1]
    fullpath = os.path.join(directory, split[0])

    return send_from_directory(fullpath, filename)



@app.route(
    "/userfile/<file_id>/thumbnail",
    methods=["GET"],
)
@login_required
def userfile_thumbnail(
    file_id,
):
    if file_id is None or file_id == 'None':
        return "File not found." #TODO: how to make 404?

    # directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
    # if directory is None:
    #     return "File not found."
    # todo: search for 2nd level directories

    # app.logger.debug("file_id: %s" % file_id)

    media_file = media.Media.query.filter_by(user_id=current_user.id, parent_id=file_id, container_type="CLEAR_THUMBNAIL").first()

    if media_file is None:
        return "File not found."
    else:
        source = media_file.source
        directory_object = UserDirectories.query.filter_by(user_id=current_user.id, platform=source).first()
        if directory_object is None:
            directory = get_user_dir(current_user, app.config["USER_DATA_DIR"], source)
        else:
            directory = directory_object.directory

    filepath = media_file.filepath
    # media_type = media_file.media_type

    # filepath = None
    # if platform == "facebook":
    #     filepath = file.filepath

    # TODO: Determine file type from DB

    if filepath is None or directory is None:
        return "File not found."

    split = os.path.split(filepath)
    filename = split[1]
    fullpath = os.path.join(directory, split[0])

    try:
        return send_from_directory(fullpath, filename)
    except Exception as e:
        if e.code == 404:
            print("Try Thumbnail creation")
            original_file = media.Media.query.filter_by(user_id=current_user.id, parent_id=file_id,
                                                     container_type="CLEAR").first()
            split_original = os.path.split(original_file.filepath)
            filename_original = split_original[1]
            create_thumbnail(directory, filename_original, original_file.media_type)
            return send_from_directory(fullpath, filename)
        else:
            raise e




@app.route(
    "/userfile/view/<container_id>",
    methods=["GET"],
)
@login_required
def userfileview(
    # platform,
    container_id,
):
    if container_id is None or container_id == 'None':
        return "File not found."
    # TODO: how to make 404 (instead of 200)?

    # directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
    # if directory is None:
    #     return "File not found."

    # app.logger.debug("file_id: %s" % file_id)

    # file = media.Media.query.filter_by(user_id=current_user.id, container_type="CONTAINER", id=file_id).first()

    media_file = media.Media.query.filter_by(user_id=current_user.id, id=container_id, container_type="CONTAINER").first()

    if media_file is None:
        return "File not found."
    else:
        source = media_file.source
        directory_object = UserDirectories.query.filter_by(user_id=current_user.id, platform=source).first()
        if directory_object is None:
            directory = get_user_dir(current_user, app.config["USER_DATA_DIR"], source)
        else:
            directory = directory_object.directory

    filepath = media_file.filepath
    # media_type = media_file.media_type

    # filepath = None
    # if platform == "facebook":
    #     filepath = file.filepath

    # TODO: Determine file type from DB

    if filepath is None or directory is None:
        return "File not found."

    split = os.path.split(filepath)
    filename = split[1]
    # fullpath = os.path.join(directory, split[0])

    # return send_from_directory(fullpath, filename)
    # files = Files.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "media/media_viewfile.html",
        media_file=media_file,
        # fullpath=fullpath,
        filename=filename,
        breadcrumb="Media / View File",
    )


@app.route("/instagram")
@login_required
def instagram():
    return render_template(
        "instagram/instagram.html",
        breadcrumb="Instagram",
    )


@app.route("/icloud")
@login_required
def icloud():
    return render_template(
        "icloud/icloud.html",
        breadcrumb="iCloud",
    )


@app.route("/google")
@login_required
def google():
    return render_template(
        "google/google.html",
        breadcrumb="Google",
    )
