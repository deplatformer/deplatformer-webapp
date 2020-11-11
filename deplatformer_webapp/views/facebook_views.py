import os
import shutil
import sqlite3
from datetime import datetime

from flask import flash, render_template, request
from flask_user import current_user, login_required
from werkzeug.utils import secure_filename

from ..app import app, db
from ..helpers import unzip
from ..helpers.facebook_helpers import clean_nametags, cut_hyperlinks, posts_to_db
from ..helpers.filecoin_helpers import push_to_filecoin
from ..models.user_models import UserDirectories
from ..services.ipfs import IPFSService


@app.route("/facebook-deplatform")
@login_required
def facebook_deplatform():
    return render_template(
        "facebook/facebook-deplatform.html",
        breadcrumb="Facebook / Deplatform",
    )


@app.route(
    "/facebook-upload",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def facebook_upload():

    # Assume upload didn't happen or failed until proven otherwise
    upload_success = False

    # Uploading a new file
    if request.method == "POST":

        # Get the filename from the request
        upload = request.files["uploadfile"]

        # Use the user data directory configured for the app
        upload_path = app.config["USER_DATA_DIR"]
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        # Create a subdirectory per username. Usernames are unique.
        user_dir = os.path.join(
            upload_path,
            str(current_user.id) + "-" + current_user.username,
        )
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        # Create a Facebook subdirectory.
        facebook_dir = os.path.join(
            user_dir,
            "facebook",
        )
        if not os.path.exists(facebook_dir):
            os.makedirs(facebook_dir)
        else:
            # Remove an existing directory to avoid dbase entry duplication
            shutil.rmtree(facebook_dir)
            os.makedirs(facebook_dir)

        # Save the uploaded file
        # TODO: move to background worker task
        file_name = secure_filename(upload.filename)
        print("Saving uploaded file")  # TODO: move to async user output
        try:
            upload.save(
                os.path.join(
                    facebook_dir,
                    file_name,
                )
            )
        except:
            # Return if the user did not provide a file to upload
            # TODO: Add flash output to facebook_upload template
            flash(
                "Please make sure that you've selected a file and that it's in ZIP format.",
                "alert-danger",
            )
            return render_template(
                "facebook/facebook-upload.html",
                upload=upload_success,
                breadcrumb="Facebook / Upload content",
            )

        # Unzip the uploaded file
        # TODO: move to background worker task
        print("Extracting zip file")  # TODO: move to async user output
        try:
            unzip_dir = unzip(
                os.path.join(
                    facebook_dir,
                    file_name,
                )
            )
            directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
            if directory is None:
                directory = UserDirectories(user_id=current_user.id, platform="facebook", directory=unzip_dir)
                db.session.add(directory)
            else:
                directory.directory = unzip_dir
            db.session.commit()

        except:
            flash(
                "Unable to extract zip file.",
                "alert-danger",
            )
            return render_template(
                "facebook/facebook-upload.html",
                upload=upload_success,
                breadcrumb="Facebook / Upload content",
            )

        # Parse Facebook JSON and save to SQLite
        # TODO: move to background worker task
        try:
            # TODO: move to async user output
            print("Parsing Facebook content.")
            # TODO: move to async user output
            print("Saving posts to database.")
            (
                total_posts,
                max_date,
                min_date,
                profile_updates,
                total_media,
            ) = posts_to_db(unzip_dir)
            # Output upload stats
            flash(
                "Saved "
                + str(total_posts[0])
                + " posts between "
                + min_date[0]
                + " and "
                + max_date[0]
                + ". This includes "
                + str(profile_updates)
                + " profile updates. "
                + str(total_media[0])
                + " media files were uploaded.",
                "alert-success",
            )
            upload_success = True
        except Exception as e:
            flash(
                "Are you sure this is a Facebook zip file? " + str(e),
                "alert-danger",
            )
            return render_template(
                "facebook/facebook-upload.html",
                upload=upload_success,
                breadcrumb="Facebook / Upload content",
            )

        # TODO: ENCRYPT FILES

        # Pin files to IPFS
        ipfs_service = IPFSService(ipfs_uri=app.config["IPFS_URI"])
        pins = ipfs_service.pin_dir(unzip_dir)

        # Add uploaded and parsed Facebook files to Filecoin
        print("Uploading files to Filecoin")
        for (
            path,
            subdirectory,
            files,
        ) in os.walk(unzip_dir):
            for file in files:
                if (file != ".DS_Store") and (file != "thumbs.db") and (file != "desktop.ini") and (file != ".zip"):
                    try:
                        push_to_filecoin(
                            path,
                            file,
                            "facebook",
                        )
                    except Exception as e:
                        flash(
                            "Unable to store " + file + " on Filecoin. " + str(e) + ".",
                            "alert-danger",
                        )

        # TODO: DELETE CACHED COPIES OF FILE UPLOADS

    return render_template(
        "facebook/facebook-upload.html",
        upload=upload_success,
        breadcrumb="Facebook / Upload content",
    )


@app.route("/facebook-view")
@login_required
def facebook_view():
    day = datetime.now().strftime("%d")
    month_script = datetime.now().strftime("%b")
    directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()

    if directory is None:
        flash(
            "Facebook data not found.",
            "alert-danger",
        )
        return render_template(
            "facebook/facebook-view.html",
            breadcrumb="Facebook / View content",
            this_day=day,
            this_month=month_script,
        )

    fb_dir = directory.directory
    db_name = os.path.basename(os.path.normpath(fb_dir))
    fb_db = fb_dir + "/" + str(db_name) + ".sqlite"

    facebook_db = sqlite3.connect(fb_db)
    cursor = facebook_db.cursor()
    cursor.execute("SELECT * FROM albums ORDER BY last_modified DESC")
    albums = cursor.fetchall()

    # Sort albums so that Profile Pictures, Cover Photos, and Videos come first
    albums_dict = {album[2]: album for album in albums}
    sorted_albums = [albums_dict[c] for c in ["Videos", "Cover Photos", "Profile Pictures"] if c in albums_dict]
    return render_template(
        "facebook/facebook-view.html",
        breadcrumb="Facebook / View content",
        this_day=day,
        this_month=month_script,
        albums=sorted_albums,
    )


@app.route("/facebook-memories")
@login_required
def facebook_memories():
    directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
    if directory is None:
        flash(
            "Facebook data not found.",
            "alert-danger",
        )
        return render_template(
            "facebook/facebook-memories.html",
            breadcrumb="Facebook / View content / Memories",
        )

    fb_dir = directory[0]
    db_name = os.path.basename(os.path.normpath(fb_dir))
    fb_db = fb_dir + "/" + str(db_name) + ".sqlite"

    day = datetime.now().strftime("%d")
    month = datetime.now().strftime("%m")
    month_script = datetime.now().strftime("%b")
    year = datetime.now().strftime("%Y")

    facebook_db = sqlite3.connect(fb_db)
    cursor = facebook_db.cursor()
    # Check if demo data is being used
    if os.path.split(fb_dir)[1][:20] == "facebook-deplatformr":
        # Prime for demo response
        cursor.execute(
            "SELECT * FROM posts WHERE strftime('%m', timestamp) = ? AND strftime('%d', timestamp) = ? ORDER BY timestamp ASC",
            (
                "08",
                "02",
            ),
        )
    else:
        cursor.execute(
            "SELECT * FROM posts WHERE strftime('%m', timestamp) = ? AND strftime('%d', timestamp) = ? ORDER BY timestamp ASC",
            (
                month,
                day,
            ),
        )
    posts = cursor.fetchall()

    media_posts = {}
    non_media_posts = {}

    for post in posts:
        if (post[3] is not None) and (post[3] > 0):

            post_year = post[1][:4]
            time_lapse = int(year) - int(post_year)
            if post[2] is not None:
                clean_post_names = clean_nametags(post[2])
                # TODO: figure out how to activate post hyperlinks within the post text
                # parsed_post, url_count = activate_hyperlinks(clean_post_names)
                (
                    parsed_post,
                    urls,
                ) = cut_hyperlinks(clean_post_names)
            else:
                parsed_post = None
                urls = None

            cursor.execute(
                "SELECT * FROM media WHERE post_id = ?",
                (post[0],),
            )
            media = cursor.fetchall()

            files = {}
            for file in media:
                if file[3] is not None:
                    if file[3] != post[2]:
                        clean_post_names = clean_nametags(file[3])
                        (
                            file_parsed_post,
                            file_urls,
                        ) = cut_hyperlinks(clean_post_names)
                    else:
                        file_parsed_post = None
                        file_urls = None
                elif (post[2] is None) or (post[2] == ""):
                    file_parsed_post = file[2]
                    file_urls = None
                else:
                    file_parsed_post = None
                    file_urls = None
                extension = os.path.splitext(file[7])
                if extension[1] == ".mp4":
                    mimetype = "video"
                else:
                    mimetype = "image"
                files.update(
                    {
                        file[0]: {
                            "file_post": file_parsed_post,
                            "urls": file_urls,
                            "mimetype": mimetype,
                        }
                    }
                )
                # reset parsed_post so that it's not re-used for entries that don't have a file[3]
                file_parsed_post = None
                file_urls = None

            media_posts.update(
                {
                    post[0]: {
                        "post_year": post_year,
                        "time_lapse": time_lapse,
                        "post": parsed_post,
                        "urls": urls,
                        "files": files,
                    }
                }
            )

            # reset parsed_post so that it's not re-used for entries that don't have a post[2]
            parsed_post = None

    if len(posts) > len(media_posts):
        for post in posts:
            if (post[3] is None) or (post[3] == 0):

                # some entries can be completely blank except for a timestamp
                if post[2] is None and post[4] is None and post[5] is None:
                    continue

                post_year = post[1][:4]
                time_lapse = int(year) - int(post_year)
                if post[2] is not None:
                    clean_post_names = clean_nametags(post[2])
                    # TODO: figure out how to activate post hyperlinks within the post text
                    # parsed_post, url_count = activate_hyperlinks(clean_post_names)
                    (
                        parsed_post,
                        urls,
                    ) = cut_hyperlinks(clean_post_names)

                if post[4] is not None and len(urls) == 0:
                    urls = []
                    urls.append(post[4])

                non_media_posts.update(
                    {
                        post[0]: {
                            "post_year": post_year,
                            "time_lapse": time_lapse,
                            "post": parsed_post,
                            "url_label": post[5],
                            "urls": urls,
                        }
                    }
                )

                # reset parsed_post so that it's not re-used for entries that don't have a post[2]
                parsed_post = None

    return render_template(
        "facebook/facebook-memories.html",
        breadcrumb="Facebook / View content / Memories",
        month_script=month_script,
        day=day,
        media_posts=media_posts,
        non_media_posts=non_media_posts,
    )


@app.route("/facebook-album/<album_id>")
@login_required
def facebook_album(
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

    fb_dir = directory.directory
    db_name = os.path.basename(os.path.normpath(fb_dir))
    fb_db = fb_dir + "/" + str(db_name) + ".sqlite"

    facebook_db = sqlite3.connect(fb_db)
    cursor = facebook_db.cursor()
    cursor.execute(
        "SELECT * FROM media WHERE album_id = ? ORDER BY timestamp DESC",
        (album_id,),
    )
    files = cursor.fetchall()
    cursor.execute(
        "SELECT * FROM albums WHERE id = ?",
        (album_id,),
    )
    album = cursor.fetchone()

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
