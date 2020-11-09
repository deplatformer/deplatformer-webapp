import os
import sqlite3

from flask import render_template, send_from_directory
from flask_user import current_user, login_required

from ..app import app


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

    try:
        deplatformr_db = sqlite3.connect("deplatformr/" + app.config["SQLALCHEMY_DATABASE_URI"][10:])
        cursor = deplatformr_db.cursor()
        cursor.execute(
            "SELECT directory FROM user_directories WHERE user_id = ? AND platform = ?",
            (
                current_user.id,
                platform,
            ),
        )
        directory = cursor.fetchone()
    except:
        return "File not found."

    try:
        platform_dir = directory[0]
        platform_db_name = os.path.basename(os.path.normpath(platform_dir))
        platform_db = platform_dir + "/" + str(platform_db_name) + ".sqlite"
        id = int(file_id)
        db = sqlite3.connect(platform_db)
        cursor = db.cursor()
        cursor.execute(
            "SELECT filepath FROM media WHERE id = ?",
            (id,),
        )
        filepath = cursor.fetchone()
    except Exception as e:
        print(e)
        return "File not found."

    split = os.path.split(filepath[0])
    filename = split[1]
    fullpath = app.config["BASEDIR"] + "/" + directory[0] + "/" + split[0] + "/"

    return send_from_directory(
        fullpath,
        filename,
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
