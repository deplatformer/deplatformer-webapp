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
    # if request.method == "POST":
        # try:
        #     facebook_dir = create_user_dirs(current_user, app.config["USER_DATA_DIR"], "facebook")
        #
        #     # TODO: This whole procedure should be async
        #     # Save the uploaded file
        #     file_name = save_upload_file(request.files["uploadfile"], facebook_dir)
        #     archive_filepath = os.path.join(facebook_dir, file_name)
        #     # Unzip the uploaded file
        #     unzip_dir = unzip(archive_filepath)
        #     # Save dirs to DB
        #     directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
        #     if directory is None:
        #         directory = UserDirectories(user_id=current_user.id, platform="facebook", directory=unzip_dir)
        #         db.session.add(directory)
        #     else:
        #         directory.directory = unzip_dir
        #     db.session.commit()
        #
        #     # TODO: ENCRYPT FILES
        #
        #     print("Saving posts to database.")
        #     (
        #         total_posts,
        #         max_date,
        #         min_date,
        #         profile_updates,
        #         total_media,
        #     ) = posts_to_db(unzip_dir)
        #
        #     flash(
        #         f"Saved {str(total_posts)} posts between {min_date} and {max_date}. This includes {str(profile_updates)} profile updates. {str(total_media)} media files were uploaded.",
        #         "alert-success",
        #     )
        #     upload_success = True
        #
        #     # Add uploaded and parsed Facebook files to Filecoin
        #     print("Encrypting and uploading files to Filecoin")
        #     derived_user_key = derive_key_from_usercreds(
        #         current_user.username.encode("utf-8"), current_user.password.encode("utf-8")
        #     )
        #     # TODO: push dir to filecoin
        #     # push_dir_to_filecoin(unzip_dir, derived_user_key)
        #
        #     # TODO: DELETE CACHED COPIES OF FILE UPLOADS
        #
        # except (IsADirectoryError, zipfile.BadZipFile):
        #     # Return if the user did not provide a file to upload
        #     # TODO: Add flash output to facebook_upload template
        #     flash(
        #         "Please make sure that you've selected a file and that it's in ZIP format.",
        #         "alert-danger",
        #     )
        # except GRPCNotAvailableException:
        #     flash(
        #         "Could not connect to Powergate Host.",
        #         "alert-danger",
        #     )
        # except Exception as e:
        #     tb = traceback.TracebackException.from_exception(e)
        #     print("".join(tb.format()))
        #     print(type(e))
        #
        #     flash(
        #         "An error occured while uploading the archive: " + str(e),
        #         "alert-danger",
        #     )

    return render_template(
        "uploader/uploader.html",
        platform="facebook",
        folder="",
        breadcrumb="Facebook / Upload content",
        user=current_user
    )

#
# @app.route("/facebook-view")
# @login_required
# def facebook_view():
#     day = datetime.now().strftime("%d")
#     month_script = datetime.now().strftime("%b")
#     directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
#
#     if directory is None:
#         flash(
#             "Facebook data not found.",
#             "alert-danger",
#         )
#         return render_template(
#             "facebook/facebook-view.html",
#             breadcrumb="Facebook / View content",
#             this_day=day,
#             this_month=month_script,
#         )
#
#     # Sort albums so that Profile Pictures, Cover Photos, and Videos come first
#     albums = media.Album.query.order_by(desc("last_modified")).all()
#     #this is where the albums are disambiguated, by album name
#     # todo: perform better unique disambiguation of albums, rather than just by name (currently can't support
#     albums_dict = {album.name: album for album in albums}
#     sorted_main_albums = [albums_dict[c] for c in ["Videos", "Cover Photos", "Profile Pictures"] if c in albums_dict]
#     sorted_main_albums_names = [c for c in ["Videos", "Cover Photos", "Profile Pictures"] if c in albums_dict]
#     sorted_other_albums = [albums_dict[d] for d in albums_dict if d not in sorted_main_albums_names]
#     app.logger.debug(sorted_main_albums)
#     return render_template(
#         "facebook/facebook-view.html",
#         breadcrumb="Facebook / View content",
#         this_day=day,
#         this_month=month_script,
#         main_albums=sorted_main_albums,
#         other_albums=sorted_other_albums,
#     )
#

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

    fb_dir = directory.directory

    day = datetime.now().strftime("%d")
    month = datetime.now().strftime("%m")
    month_script = datetime.now().strftime("%b")
    year = datetime.now().strftime("%Y")

    facebook_db = sqlite3.connect(app.config["MEDIA_SQLITE_DB"])
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
                mimetype = "video" if extension[1] == ".mp4" else "image"
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
