import json
import os
import re
import shutil
from datetime import datetime

import ftfy
# from flask import app
from sqlalchemy import asc, desc
from werkzeug.utils import secure_filename
import ffmpeg
from PIL import Image

from deplatformer_webapp.models.media import Media

from ..app import db as appdb
from ..models import media


def save_file(app, media_file, media_info, media_dir, data_dir):
    # appdb = app.db
    # FB might include more than one posts JSON file
    # files = os.listdir(fb_dir + "/posts/")

    #todo: check album
        #todo: then create album
        #todo: store created album flag

# save the file
    filepath = save_upload_file(media_file, media_dir, media_info.get("name", ""), media_info, data_dir)

    # TODO: Get exif
    # create thumbnail

    thumbpath = create_thumbnail(data_dir, filepath)

    thumbnail_media_type = "THUMBNAIL"

    thumbnail = media.Media(
        filepath=thumbpath,
        media_type=thumbnail_media_type,
    )
    appdb.session.add(thumbnail)
    appdb.session.commit()

    # "relativePath": metadata.get("relativePath", ""),
    # "name": metadata.get("name", ""),
    # "type": metadata.get("type", "text/none"),
    # "tags": metadata.get("tags", ""),
    # "description": metadata.get("description", ""),
    # "platform": metadata.get("platform"),

    # todo: add tags
    # todo: add albums

    new_media_obj = media.Media(
        # timestamp=media_obj.get("timestamp"),
        description=media_info.get("description", None),
        filepath=filepath,
        # post_id=post_id,
        thumbnail=thumbnail.id,
        title=media_info.get("name", None)
        # timestamp=timestamp,
        # post=post,
        # url=url,
        # url_label=url_label,
        # place_name=place_name,
        # address=address,
        # latitude=latitude,
        # longitude=longitude,
        # profile_update=profile_update,
    )
    appdb.session.add(new_media_obj)
    appdb.session.commit()
    # except Exception as e:
    #     print("couldn't update media file with post id")
    #     print(e)
# except:
#     # Profile update does not have a media file attached, so don't include it
#     # continue

    # Recount total number of posts
    # total_posts = len(media.Post.query.all())
    #
    # # Calculate total number of profile updates
    # profile_updates = total_posts - subtotal_posts
    #
    # # Get latest post date
    # max_date = media.Post.query.order_by(desc("timestamp")).first().timestamp
    #
    # # Get first post date
    # min_date = media.Post.query.order_by(asc("timestamp")).first().timestamp
    #
    # # Count total number of media files
    # total_media = len(media.Media.query.all())

    #todo: use created album flag and update the album with this photo

    return (
        # total_posts,
        # max_date,
        # min_date,
        # profile_updates,
        # total_media,
    )

#
# def albums_to_db(fb_dir):
#     # FB includes one JSON file per album
#     files = os.listdir(fb_dir + "/photos_and_videos/album/")
#     for file in files:
#         file_split = os.path.splitext(file)
#         if file_split[1] == ".json":
#             # Read data from FB JSON file
#             with open(os.path.join(fb_dir + "/photos_and_videos/album/" + file)) as f:
#                 album_contents = json.load(f)
#
#             unix_time = album_contents.get("last_modified_timestamp", None)
#             last_modified = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S") if unix_time else None
#             description = album_contents.get("description", None)
#             name = album_contents.get("name", None)
#             cover_photo = None  # get Media file id to use as foreign key
#
#             # Save album info
#             album = media.Album(
#                 name=name,
#                 description=description,
#                 last_modified=last_modified,
#                 cover_photo_id=cover_photo,
#             )
#             appdb.session.add(album)
#             appdb.session.commit()
#
#             for photo in album_contents["photos"]:
#                 filepath = photo.get("uri", None)
#                 if filepath is None or filepath[:18] != "photos_and_videos/":  # Don't inlude links to external images
#                     continue
#
#                 unix_time = photo.get("creation_timestamp", None)
#                 timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S") if unix_time else None
#                 title = ftfy.fix_text(photo["title"]) if photo.get("title") else None
#                 description = ftfy.fix_text(photo["description"]) if photo.get("description") else None
#                 latitude = photo.get("media_metadata", {}).get("photo_metadata", {}).get("latitude", None)
#                 longitude = photo.get("media_metadata", {}).get("photo_metadata", {}).get("longitude", None)
#                 orientation = photo.get("media_metadata", {}).get("photo_metadata", {}).get("orientation", None)
#                 media_type = "IMAGE"
#
#                 # TODO: Get exif
#                 # create thumbnail
#
#                 thumbpath = create_thumbnail(fb_dir, filepath)
#
#                 thumbnail_media_type = "THUMBNAIL"
#
#                 thumbnail = media.Media(
#                     timestamp=timestamp,
#                     title=title,
#                     description=description,
#                     filepath=thumbpath,
#                     post_id=None,
#                     album_id=album.id,
#                     media_type=thumbnail_media_type,
#                 )
#                 appdb.session.add(thumbnail)
#                 appdb.session.commit()
#
#                 media = media.Media(
#                     timestamp=timestamp,
#                     title=title,
#                     description=description,
#                     latitude=latitude,
#                     longitude=longitude,
#                     orientation=orientation,
#                     filepath=filepath,
#                     post_id=None,
#                     album_id=album.id,
#                     media_type=media_type,
#                     thumbnail=thumbnail.id,
#                 )
#                 appdb.session.add(media)
#                 appdb.session.commit()
#
#             total_files = len(media.Media.query.filter_by(album_id=album.id).all())
#             if total_files == 0:
#                 # Delete albums that have zero files
#                 appdb.session.delete(album)
#                 appdb.session.commit()
#                 continue
#
#             # Get cover photo id for this album
#             cover_photo = media.Media.query.filter_by(filepath=album_contents["cover_photo"]["uri"]).first()
#             album.total_files = total_files
#             album.cover_photo_id = cover_photo.thumbnail  #cover_photo.id
#
#             appdb.session.commit()
#
#
#
#     # Include the video directory
#     if os.path.isdir(fb_dir + "/photos_and_videos/videos/"):
#         album = media.Album(name="Videos")
#         appdb.session.add(album)
#         appdb.session.commit()
#
#         if os.path.isfile(fb_dir + "/photos_and_videos/your_videos.json"):
#             with open(fb_dir + "/photos_and_videos/your_videos.json") as f:
#                 videos = json.load(f)
#
#             for video in videos["videos"]:
#                 filepath = video.get("uri", None)
#                 if filepath is None or filepath[:18] != "photos_and_videos/":
#                     continue
#                 unix_time = video.get("creation_timestamp", None)
#                 timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S") if unix_time else None
#                 description = video.get("description", None)
#                 title = "Video"
#                 media_type = "VIDEO"
#                 thumbnail_media_type = "THUMBNAIL"
#
#                 print("Video:  Filepath: %s, %s" % (fb_dir, filepath))
#                 osfilepath = os.path.join(fb_dir, filepath)
#
#                 split = os.path.splitext(filepath)
#                 thumbpath = "".join([split[0], split[1], '.thumb', '.jpg'])
#
#                 osfileoutpath = os.path.join(fb_dir, thumbpath)
#                 print("Video:  Thumbpath: %s" % thumbpath)
#
#                 # https://mhsiddiqui.github.io/2018/02/09/Using-FFmpeg-to-create-video-thumbnails-in-Python/
#                 # https://github.com/kkroening/ffmpeg-python/blob/master/examples/README.md#generate-thumbnail-for-video
#                 # https://trac.ffmpeg.org/wiki/Create%20a%20thumbnail%20image%20every%20X%20seconds%20of%20the%20video
#
#                 ff = (
#                     ffmpeg
#                         .input(osfilepath)
#                         .filter('scale', "640", -1)
#                         .output(osfileoutpath, vframes=1)
#                 )
#
#                 print(ff)
#
#                 ff.run()
#
#                 thumbnail = media.Media(
#                     timestamp=timestamp,
#                     title=title,
#                     description=description,
#                     filepath=thumbpath,
#                     post_id=None,
#                     album_id=album.id,
#                     media_type=thumbnail_media_type,
#                 )
#                 appdb.session.add(thumbnail)
#                 appdb.session.commit()
#
#                 media = media.Media(
#                     timestamp=timestamp,
#                     title=title,
#                     description=description,
#                     filepath=filepath,
#                     album_id=album.id,
#                     media_type=media_type,
#                     thumbnail=thumbnail.id,
#                 )
#                 appdb.session.add(media)
#                 appdb.session.commit()
#
#         # Count total number of videos in this album
#         total_files = len(media.Media.query.filter_by(album_id=album.id).all())
#
#         # Use the first video's thumbnail as a cover for the album
#         cover_video = media.Media.query.filter((media.Media.album_id == album.id) & (media.Media.media_type == "VIDEO")).first()
#         cover_video_thumbnail = cover_video.thumbnail
#
#         # Update album record with number of videos and cover video
#         album.total_files = total_files
#         album.cover_photo_id = cover_video_thumbnail
#         appdb.session.commit()


def create_user_dirs(user, base_path, media_source):
    # Use the user data directory configured for the app
    upload_path = base_path
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    # Create a subdirectory per username. Usernames are unique.
    user_dir = os.path.join(
        upload_path,
        str(user.id) + "-" + user.username,
    )
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    # Create a Facebook subdirectory.
    media_dir = os.path.join(
        user_dir,
        media_source,
    )
    if os.path.exists(media_dir):
        # Remove an existing directory to avoid dbase entry duplication
        # shutil.rmtree(media_dir) # todo: HIGH PRIORITY fix this for duplicate facebook zips
        print("Path exists")
    else:
        os.makedirs(media_dir)
    return media_dir


def save_upload_file(upload_file, directory, name="", media_info=None, data_dir=""):
    # todo:  Name security Please HIGH PRIORITY
    if name == "":
        file_name = secure_filename(upload_file.filename)
    else:
        file_name = name  # todo: sanitize name
    print("Saving uploaded file")  # TODO: move to async user output / call return?
    destination = os.path.join(data_dir, file_name,)
    if upload_file is not None:
        upload_file.save(destination)
    elif media_info is not None:
        shutil.move(media_info.get("file_location"), destination, copy_function=shutil.copy)  # use copy instead of copy2 to ensure it copies (we don't need the metadata for an uploaded file)
    else:
        raise FileNotFoundError()  # todo: should this be a file not found error?
    return file_name


def create_thumbnail(fb_dir, filepath):
    print("Image:  Filepath: %s, %s" % (fb_dir, filepath))
    osfilepath = os.path.join(fb_dir, filepath)

    split = os.path.splitext(filepath)
    thumbpath = "".join([split[0], split[1], '.thumb', '.jpg'])

    osfileoutpath = os.path.join(fb_dir, thumbpath)
    print("Image:  Thumbpath: %s" % thumbpath)

    # open file
    image = Image.open(osfilepath)
    # Image.open('image.gif').convert('RGB').save('image.jpg')
    #
    # #check if gif
    # image = check_gif(image)

    # make a copy
    im = image.copy()
    # check mode, if not then convert it
    if not im.mode == 'RGB':
        im = im.convert('RGB')
    # now thumbnail it
    im.thumbnail((640, 480), resample=Image.HAMMING)
    im.save(osfileoutpath, "JPEG", quality=30)

    return thumbpath


def check_gif(image):
    try:
        image.seek(1)
        frame = 1
        multiframe = True
    except EOFError:
        print('Warning: it is a single frame GIF.')
        frame = 0
        multiframe = False

    # if multiframe
    current_index = image.tell()
    return image.seek(current_index)


def handle_uploaded_file(app, tmpfileid, user):

    metadata_file_location = os.path.join("tmp/" + tmpfileid + ".info")
    file_location = os.path.join("tmp/" + tmpfileid)
    with open(metadata_file_location) as f:  # todo: config this
        info_file = json.load(f)
        metadata = info_file.get("upload_metadata", None)

    # todo: except empty metadata

    # flaskapp.app_context().push()
#
#     # TODO: This whole procedure should be async
#     # Save the uploaded file
    media_info = {  # todo: sanitise input?
        "relativePath": metadata.get("relativePath", ""),
        "name": metadata.get("name", ""),
        "type": metadata.get("type", "text/none"),
        "tags": metadata.get("tags", ""),
        "description": metadata.get("description", ""),
        "platform": metadata.get("platform"),
        "file_id": tmpfileid,
        "file_location": file_location,
        "metadata_file_location": metadata_file_location
    }

    media_dir = create_user_dirs(user, app.config["USER_DATA_DIR"], media_info.get("platform", "media"))
#     # file_name = save_upload_file(request.files['files[]'], media_dir)
#     # archive_filepath = os.path.join(media_dir, uploaded_file)
#     # TODO: detect filetype archive
#     # Unzip the uploaded file
#     # unzip_dir = unzip(archive_filepath)
#     # Save dirs to DB
#     # directory = UserDirectories.query.filter_by(user_id=current_user.id, platform=platform).first()
#     # if directory is None:
#     #     directory = UserDirectories(user_id=current_user.id, platform=platform, directory=platform)
#     #     db.session.add(directory)
#     # else:
#     #     directory.directory = platform
#     # db.session.commit()
#
#     # TODO: ENCRYPT FILES
#
#     # print("Saving posts to database.")
#     # (
#     #     total_posts,
#     #     max_date,
#     #     min_date,
#     #     profile_updates,
#     #     total_media,
#     # ) = posts_to_db(unzip_dir)
#     file = None
#     with open(os.path.join("tmp/" + tmpfileid), mode='r+b') as f:  # todo: config this
#         file = f
#     if file is not None:
    save_file(app, None, media_info, media_info.get("platform", "media"), media_dir)
    #     upload_success = True
    # else:
    #     upload_success = False
#
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
# #
# # except (IsADirectoryError, zipfile.BadZipFile):
# #     # Return if the user did not provide a file to upload
# #     # TODO: Add flash output to facebook_upload template
# #     flash(
# #         "Please make sure that you've selected a file and that it's in ZIP format.",
# #         "alert-danger",
# #     )
# # except GRPCNotAvailableException:
# #     flash(
# #         "Could not connect to Powergate Host.",
# #         "alert-danger",
# #     )