import os
import sqlite3

from flask import render_template, send_from_directory
from flask_user import current_user, login_required

from ..app import app, db
from ..crypto import create_user_key_if_not_exists
from ..models import facebook
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
    "/userfile/<platform>/<file_id>",
    methods=["GET"],
)
@login_required
def userfile(
    platform,
    file_id,
):
    if file_id is None or file_id == 'None':
        return "File not found." #TODO: how to make 404?

    directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
    if directory is None:
        return "File not found."

    #app.logger.debug("file_id: %s" % file_id)

    filepath = None
    if platform == "facebook":
        filepath = facebook.Media.query.filter_by(id=file_id).first().filepath

    if filepath is None:
        return "File not found."

    split = os.path.split(filepath)
    filename = split[1]
    fullpath = os.path.join(app.config["USER_DATA_DIR"], directory.directory, split[0])

    return send_from_directory(fullpath, filename)



@app.route(
    "/userfile/<platform>/view/<file_id>",
    methods=["GET"],
)
@login_required
def userfileview(
    platform,
    file_id,
):
    if file_id is None or file_id == 'None':
        return "File not found."
    # TODO: how to make 404 (instead of 200)?

    directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
    if directory is None:
        return "File not found."

    # app.logger.debug("file_id: %s" % file_id)

    file = facebook.Media.query.filter_by(id=file_id).first()

    if file is None:
        return "File not found in DB."

    filepath = None
    if platform == "facebook":
        filepath = file.filepath

    # TODO: Determine file type from DB

    if filepath is None:
        return "File not found."

    split = os.path.split(filepath)
    filename = split[1]
    fullpath = os.path.join(app.config["USER_DATA_DIR"], directory.directory, split[0])

    # return send_from_directory(fullpath, filename)
    # files = Files.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "media/media_view.html",
        file=file,
        fullpath=fullpath,
        filename=filename,
        breadcrumb="Filecoin / Files",
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
