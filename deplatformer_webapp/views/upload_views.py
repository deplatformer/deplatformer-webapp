import os
import sqlite3
import traceback
import zipfile
from datetime import datetime

from flask import flash, render_template, request
from flask_user import current_user, login_required
from pygate_grpc.exceptions import GRPCNotAvailableException
from sqlalchemy import desc

from deplatformer_webapp.crypto import derive_key_from_usercreds

from ..app import app, db
from ..helpers import unzip
from ..helpers.mediafile_helpers import create_user_dirs, save_file
# from ..helpers.filecoin_helpers import push_dir_to_filecoin
from ..models import media
from ..models.user_models import UserDirectories

@app.route("/upload")
@login_required
def media():

    return render_template(
        "uploader/uploader.html",
        breadcrumb="All Media / Upload",
        user=current_user
    )


# @app.route(
#     "/media-upload/",
#     methods=[
#         "GET",
#         "POST",
#     ],
# )
# # @login_required
# # def media_upload():
# #     platform = "media"
# #
# #     # Assume upload didn't happen or failed until proven otherwise
# #     upload_success = False
# #
# #     # Uploading a new file
# #     if request.method == "POST":
# #         try:
# #
# #         except Exception as e:
# #             tb = traceback.TracebackException.from_exception(e)
# #             print("".join(tb.format()))
# #             print(type(e))
# #
# #             flash(
# #                 "An error occured while uploading the archive: " + str(e),
# #                 "alert-danger",
# #             )
# #
# #     #TODO: Return json
# #     return render_template(
# #         "facebook/facebook-upload.html",
# #         upload=upload_success,
# #         breadcrumb="Facebook / Upload content",
# #     )

#
# @app.route("/facebook-view")
# @login_required
# def media_view():
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
#         "media/media-view.html",
#         breadcrumb="All Media / View content",
#         main_albums=sorted_main_albums,
#         other_albums=sorted_other_albums,
#     )
#
#
#
# @app.route("/media-manage")
# @login_required
# def media_manage():
#     return render_template(
#         "media/media-manage.html",
#         breadcrumb="All Media / Manage content",
#     )
