import os
import sqlite3

from flask import render_template, send_from_directory
from flask_user import current_user, login_required

from ..app import app
from ..models.user_models import UserDirectories


@app.route("/")
@login_required
def homepage():
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
    directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
    if directory is None:
        return "File not found."

    try:
        platform_dir = directory.directory
        platform_db_name = os.path.basename(os.path.normpath(platform_dir))
        platform_db = platform_dir + "/" + str(platform_db_name) + ".sqlite"
        db = sqlite3.connect(platform_db)
        cursor = db.cursor()
        cursor.execute(
            "SELECT filepath FROM media WHERE id = ?",
            (int(file_id),),
        )
        filepath = cursor.fetchone()
    except Exception as e:
        print(e)
        return "File not found."

    split = os.path.split(filepath[0])
    filename = split[1]
    fullpath = os.path.join(app.config["USER_DATA_DIR"], directory.directory, split[0])
    return send_from_directory(fullpath, filename)


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
