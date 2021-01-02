import json
import os
import re
import traceback
import shutil
import zipfile
from datetime import datetime

import ftfy
from flask import app
from sqlalchemy import asc, desc
from werkzeug.utils import secure_filename

from ..helpers import unzip
import ffmpeg
from PIL import Image
from ..models.user_models import UserDirectories
from deplatformer_webapp.crypto import derive_key_from_usercreds

from deplatformer_webapp.models.media import Media
from .media_helpers import create_thumbnail, get_thumbnailpath

from ..app import db as appdb
from ..models import media


def activate_hyperlinks(
        post,
):
    urls = re.findall(r"(https?://\S+)", post)
    for url in urls:
        post = post.replace(url, "")
    return post, len(urls)


def cut_hyperlinks(
        post,
):
    urls = re.findall(r"(https?://\S+)", post)
    cleaned_post, start = post, 0
    for url in urls:
        idx = post.find(url, start)
        cleaned_post += post[:idx] + post[idx + len(url):]
        start = idx + len(url)
    return cleaned_post, urls


def clean_nametags(
        post,
):
    post_length = len(post)
    post_slice = post
    slice_length = post_length
    i = 0
    colon_count = 0

    while i < post_length:
        tagged_name = ""
        nametag = post_slice.find("@[")

        if nametag == -1:
            break

        for i in range(
                nametag,
                slice_length,
        ):
            tagged_name += post_slice[i]
            if i == slice_length - 1:
                break
            if post_slice[i + 1] == ":":
                colon_count += 1
                if colon_count == 2:
                    tagged_name += post_slice[i + 1]
                    break

        post = post.replace(
            tagged_name,
            "",
        )

        post_slice = post_slice[
            slice(
                i + 2,
                post_length,
            )
        ]
        name_end = post_slice.find("]")

        name = post_slice[
            slice(
                0,
                name_end,
            )
        ]

        post = post.replace(
            name + "]",
            "<span class='name'>" + name + "</span>",
        )

        post_slice = post_slice[
            slice(
                name_end + 1,
                post_length,
            )
        ]
        slice_length = len(post_slice)
        colon_count = 0

    return post


def posts_to_db(fb_dir, facebook_node, current_user):
    print("Parsing Facebook content.")
    # Get or make default top lv facebook folder

    # Add albums with media files first so they can be referenced from posts
    albums_to_db(fb_dir, facebook_node, current_user)

    # FB might include more than one posts JSON file
    files = os.listdir(fb_dir + "/posts/")
    for file in files:
        file_split = os.path.splitext(file)
        if (file_split[0][:10] == "your_posts") and (file_split[1] == ".json"):
            # Read data from FB JSON file
            with open(os.path.join(fb_dir + "/posts/" + file)) as f:
                posts = json.load(f)

            for content in posts:
                unix_time = content["timestamp"]
                timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")

                try:
                    post_source = content["data"][0]["post"]
                    # Clean up FB's garbage UTF-8 (Mojibake)
                    post = ftfy.fix_text(post_source)
                except:
                    post = content.get("title", None)

                url = None
                url_label = None
                place_name = None
                address = None
                latitude = None
                longitude = None
                media_files = None

                try:
                    attachment_sections = len(content["attachments"])
                    for i in range(
                            0,
                            attachment_sections,
                    ):
                        if i == 0:
                            try:
                                url = content["attachments"][0]["data"][0]["external_context"]["url"]
                            except:
                                pass
                            try:
                                url_label_source = content["attachments"][0]["data"][0]["external_context"]["name"]
                                url_label = ftfy.fix_text(url_label_source)

                            except:
                                pass
                        if i == 1:
                            try:
                                place_name_source = content["attachments"][1]["data"][0]["place"]["name"]
                                place_name = ftfy.fix_text(place_name_source)
                            except:
                                pass
                            try:
                                address = content["attachments"][1]["data"][0]["place"]["address"]
                            except:
                                pass
                            try:
                                latitude = content["attachments"][1]["data"][0]["place"]["coordinate"]["latitude"]
                            except:
                                pass
                            try:
                                longitude = content["attachments"][1]["data"][0]["place"]["coordinate"]["longitude"]
                            except:
                                pass
                except:
                    pass

                profile_update = False

                # TODO: use PIL exif

                if timestamp is not None:
                    # # create and use thumbnail
                    #
                    # thumbpath = create_thumbnail(fb_dir, filepath)
                    #
                    # thumbnail_media_type = "THUMBNAIL"
                    #
                    # thumbnail = facebook.Media(
                    #     timestamp=timestamp,
                    #     # title=title,
                    #     # description=description,
                    #     filepath=thumbpath,
                    #     post_id=None,
                    #     media_type=thumbnail_media_type,
                    # )
                    # appdb.session.add(thumbnail)
                    # appdb.session.commit()

                    fb_post = media.Post(
                        timestamp=timestamp,
                        post=post,
                        url=url,
                        url_label=url_label,
                        place_name=place_name,
                        address=address,
                        latitude=latitude,
                        longitude=longitude,
                        profile_update=profile_update,
                        # thumbnail=thumbnail.id,
                    )
                    appdb.session.add(fb_post)
                    appdb.session.commit()

                    # Get current post_id
                    post_id = fb_post.id

                try:
                    attachments = content["attachments"][0]["data"]
                    count = len(attachments)

                    for i in range(
                            0,
                            count,
                    ):
                        attachment = content["attachments"][0]["data"][i]
                        for (
                                key,
                                value,
                        ) in attachment.items():
                            if key == "media":
                                try:
                                    # match filepath to an existing media record
                                    filepath = value["uri"]
                                    media_file = media.Media.query.filter_by(filepath=filepath, container_type="CONTAINER").first()
                                    # Update media record with post_id
                                    # media_obj = media.Media.query.filter_by(id=media_file)
                                    media_file.post_id = post_id
                                    appdb.session.commit()

                                except Exception as e:
                                    print(str(post_id) + ": media file not found")

                    # Count total number of media files for this post
                    total_files = len(media.Media.query.filter_by(post_id=post_id).all())

                    # Update post record with number of media files
                    fb_post.media_files = total_files
                    appdb.session.commit()

                except:
                    pass

    # Count total number of posts
    subtotal_posts = len(media.Post.query.all())

    print("Adding profile updates.")

    # Load FB profile update history
    f = open(os.path.join(fb_dir + "/profile_information/profile_update_history.json"))
    profile_updates = json.load(f)
    updates = profile_updates["profile_updates"]

    for update in updates:
        try:
            # Check whether the update is linked to a media file, if not, loop will continue
            filepath = update["attachments"][0]["data"][0]["media"]["uri"]
            media_obj = media.Media.query.filter_by(filepath=filepath, container_type="CONTAINER").first()
            if media_obj == None:
                # Update is not linked to a media file
                continue
            new_media = media_obj.post_id is not None

            # Get profile update metadata
            unix_time = update.get("timestamp", None)
            timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S") if unix_time else None
            title = update.get("title", None)

            # Save profile update as post
            new_post = media.Post(timestamp=timestamp, post=title, media_files=1, profile_update=True)
            appdb.session.add(new_post)
            appdb.session.commit()

            post_id = new_post.id

            try:
                if new_media == False:
                    # Update existing media record with post_id
                    media_obj.post_id = post_id
                else:
                    # TODO: Get exif
                    # create thumbnail

                    thumbpath = create_thumbnail(fb_dir, filepath)

                    thumbnail_media_type = "THUMBNAIL"

                    thumbnail = media.Media(
                        timestamp=timestamp,
                        title=title,
                        # description=description,
                        filepath=thumbpath,
                        post_id=None,
                        media_type=thumbnail_media_type,
                    )
                    appdb.session.add(thumbnail)
                    appdb.session.commit()

                    new_media_obj = media.Media(
                        timestamp=media_obj.timestamp,
                        description=media_obj.description,
                        filepath=filepath,
                        post_id=post_id,
                        thumbnail=thumbnail.id
                    )
                    appdb.session.add(new_media_obj)
                appdb.session.commit()
            except Exception as e:
                print("couldn't update media file with post id")
                print(e)
        except:
            # Profile update does not have a media file attached, so don't include it
            continue

    # Recount total number of posts
    total_posts = len(media.Post.query.all())

    # Calculate total number of profile updates
    profile_updates = total_posts - subtotal_posts

    # Get latest post date
    max_date = media.Post.query.order_by(desc("timestamp")).first().timestamp

    # Get first post date
    min_date = media.Post.query.order_by(asc("timestamp")).first().timestamp

    # Count total number of media files
    total_media = len(media.Media.query.all())

    return (
        total_posts,
        max_date,
        min_date,
        profile_updates,
        total_media,
    )


def albums_to_db(fb_dir, facebook_node, current_user):
    from .mediafile_helpers import register_media
    # FB includes one JSON file per album
    source = "FACEBOOK"
    files = os.listdir(fb_dir + "/photos_and_videos/album/")
    for file in files:
        file_split = os.path.splitext(file)
        if file_split[1] == ".json":
            # Read data from FB JSON file
            with open(os.path.join(fb_dir + "/photos_and_videos/album/" + file)) as f:
                album_contents = json.load(f)

            unix_time = album_contents.get("last_modified_timestamp", None)
            last_modified = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S") if unix_time else None
            description = album_contents.get("description", None)
            name = album_contents.get("name", None)
            cover_photo = None  # get Media file id to use as foreign key

            album = Media.query.filter_by(user_id=current_user.id, parent_id=facebook_node.id,
                                          container_type="ALBUM", source=source,
                                          name=name, last_modified=last_modified).first()
            if album is None:
                # Save album info
                album = Media(
                    user_id=current_user.id,
                    parent_id=facebook_node.id,
                    name=name,
                    description=description,
                    last_modified=last_modified,
                    # cover_photo_id=cover_photo,
                    source=source,
                    container_type="ALBUM",
                )
                appdb.session.add(album)
                appdb.session.commit()

            for photo in album_contents["photos"]:
                filepath = photo.get("uri", None)
                if filepath is None or filepath[:18] != "photos_and_videos/":  # Don't inlude links to external images
                    continue

                unix_time = photo.get("creation_timestamp", None)
                timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S") if unix_time else None
                name = ftfy.fix_text(photo["title"]) if photo.get("title") else None
                description = ftfy.fix_text(photo["description"]) if photo.get("description") else None
                latitude = photo.get("media_metadata", {}).get("photo_metadata", {}).get("latitude", None)
                longitude = photo.get("media_metadata", {}).get("photo_metadata", {}).get("longitude", None)
                orientation = photo.get("media_metadata", {}).get("photo_metadata", {}).get("orientation", None)
                # media_type =

                media_object = {
                    "name": name,
                    "description": description,
                    "source": source,
                    "last_modified": last_modified,
                    "timestamp": timestamp,
                    "media_path": fb_dir,
                    "filepath": filepath,
                    "latitude": latitude,
                    "longitude": longitude,
                    "orientation": orientation,
                    "media_type": "IMAGE",
                }

                register_media(media_object, current_user, album)

                # todo: store information in .info file
                # todo: add file to queue for encryption

            # total_files = len(Media.query.filter_by(album_id=album.id).all())
            # if total_files == 0:
            #     # Delete albums that have zero files
            #     appdb.session.delete(album)
            #     appdb.session.commit()
            #     continue

            # Get cover photo id for this album
            # cover_photo = Media.query.filter_by(filepath=album_contents["cover_photo"]["uri"]).first()
            # album.total_files = total_files
            # album.cover_photo_id = cover_photo.thumbnail  # cover_photo.id

            # appdb.session.commit()

    # FB includes one directory of images that does not have a JSON file
    # Save 'your_posts' as an album
    if os.path.isdir(fb_dir + "/photos_and_videos/your_posts/"):
        album = Media.query.filter_by(user_id=current_user.id, parent_id=facebook_node.id,
                                      container_type="ALBUM", source=source,
                                      name="Your Posts").first()
        if album is None:
            # Save album info
            album = Media(
                user_id=current_user.id,
                parent_id=facebook_node.id,
                name="Your Posts",
                # description=description,
                # last_modified=last_modified,
                # cover_photo_id=cover_photo,
                source=source,
                container_type="ALBUM",
            )
            appdb.session.add(album)
            appdb.session.commit()

        # album = Album(name="Your Posts")
        # appdb.session.add(album)
        # appdb.session.commit()

        files = os.listdir(fb_dir + "/photos_and_videos/your_posts/")
        for file in files:
            filepath = "photos_and_videos/your_posts/" + file
            # media = media.Media(filepath=filepath, album_id=album.id)
            # appdb.session.add(media)
            # appdb.session.commit()
            media_object = {
                "source": source,
                "media_path": fb_dir,
                "filepath": filepath,
                "media_type": "IMAGE",
            }
            register_media(media_object, current_user, album)

        # Count total number of photos for this album
        # total_files = len(media.Media.query.filter_by(album_id=album.id).all())

        # Use the first photo as a cover for the album
        # cover_photo = media.Media.query.filter_by(album_id=album.id).first()

        # Update album record with number of photos and cover photo
        # album.total_files = total_files
        # album.cover_photo = cover_photo.thumbnail  # cover_photo.id
        # appdb.session.commit()

    # Include the video directory
    if os.path.isdir(fb_dir + "/photos_and_videos/videos/"):
        # album = media.Album(name="Videos")
        album = Media.query.filter_by(user_id=current_user.id, parent_id=facebook_node.id,
                                      container_type="ALBUM", source=source,
                                      name="Your Videos").first()
        if album is None:
            # Save album info
            album = Media(
                user_id=current_user.id,
                parent_id=facebook_node.id,
                name="Your Videos",
                # description=description,
                # last_modified=last_modified,
                # cover_photo_id=cover_photo,
                source=source,
                container_type="ALBUM",
            )
            appdb.session.add(album)
            appdb.session.commit()

        # appdb.session.add(album)
        # appdb.session.commit()

        if os.path.isfile(fb_dir + "/photos_and_videos/your_videos.json"):
            with open(fb_dir + "/photos_and_videos/your_videos.json") as f:
                videos = json.load(f)

            for video in videos["videos"]:
                filepath = video.get("uri", None)
                if filepath is None or filepath[:18] != "photos_and_videos/":
                    continue
                unix_time = video.get("creation_timestamp", None)
                timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S") if unix_time else None
                description = video.get("description", None)
                name = "Your Video"

                media_object = {
                    "source": source,
                    "timestamp": timestamp,
                    "name": name,
                    "description": description,
                    "media_path": fb_dir,
                    "filepath": filepath,
                    "media_type": "VIDEO",
                }
                register_media(media_object, current_user, album)


                #
                # print("Video:  Filepath: %s, %s" % (fb_dir, filepath))
                # osfilepath = os.path.join(fb_dir, filepath)
                #
                # split = os.path.splitext(filepath)
                # thumbpath = "".join([split[0], split[1], '.thumb', '.jpg'])
                #
                # osfileoutpath = os.path.join(fb_dir, thumbpath)
                # print("Video:  Thumbpath: %s" % thumbpath)
                #
                # # https://mhsiddiqui.github.io/2018/02/09/Using-FFmpeg-to-create-video-thumbnails-in-Python/
                # # https://github.com/kkroening/ffmpeg-python/blob/master/examples/README.md#generate-thumbnail-for-video
                # # https://trac.ffmpeg.org/wiki/Create%20a%20thumbnail%20image%20every%20X%20seconds%20of%20the%20video
                #
                # ff = (
                #     ffmpeg
                #         .input(osfilepath)
                #         .filter('scale', "640", -1)
                #         .output(osfileoutpath, vframes=1)
                # )
                #
                # print(ff)
                #
                # ff.run()
                #
                # thumbnail = media.Media(
                #     timestamp=timestamp,
                #     title=title,
                #     description=description,
                #     filepath=thumbpath,
                #     post_id=None,
                #     album_id=album.id,
                #     media_type=thumbnail_media_type,
                # )
                # appdb.session.add(thumbnail)
                # appdb.session.commit()
                #
                # media = media.Media(
                #     timestamp=timestamp,
                #     title=title,
                #     description=description,
                #     filepath=filepath,
                #     album_id=album.id,
                #     media_type=media_type,
                #     thumbnail=thumbnail.id,
                # )
                # appdb.session.add(media)
                # appdb.session.commit()

        # Count total number of videos in this album
        # total_files = len(media.Media.query.filter_by(album_id=album.id).all())

        # Use the first video's thumbnail as a cover for the album
        # cover_video = media.Media.query.filter(
        #     (media.Media.album_id == album.id) & (media.Media.media_type == "VIDEO")).first()
        # cover_video_thumbnail = cover_video.thumbnail

        # Update album record with number of videos and cover video
        # album.total_files = total_files
        # album.cover_photo_id = cover_video_thumbnail
        # appdb.session.commit()


def upload_facebook_file(current_user, file_name, media_dir):
    from .mediafile_helpers import register_media
    try:
        # facebook_dir = create_user_dirs(current_user, app.config["USER_DATA_DIR"], "facebook")

        # TODO: This whole procedure should be async
        # Save the uploaded file
        # file_name = save_upload_file(request.files["uploadfile"], facebook_dir)
        archive_filepath = os.path.join(media_dir, file_name)
        # Unzip the uploaded file
        unzip_dir = unzip(archive_filepath)
        # Save dirs to DB
        top_node = Media.query.filter_by(user_id=current_user.id, parent_id=None, container_type="ALBUM").first()
        if top_node is None:
            top_node = Media(
                user_id=current_user.id,
                name="Top",
                description="Media",
                container_type="ALBUM",
                parent_id=None,
                source=None,
            )
            appdb.session.add(top_node)
            appdb.session.commit()
        directory = UserDirectories.query.filter_by(user_id=current_user.id, platform="facebook").first()
        if directory is None:
            directory = UserDirectories(user_id=current_user.id, platform="facebook", directory=unzip_dir)
            appdb.session.add(directory)
            appdb.session.commit()
        else:
            directory.directory = unzip_dir

        facebook_node = Media.query.filter_by(user_id=current_user.id, parent_id=top_node.id, container_type="ALBUM",
                                              source="FACEBOOK").first()
        if facebook_node is None:
            facebook_node = Media(
                user_id=current_user.id,
                name="Facebook",
                description="Facebook Media",
                container_type="ALBUM",
                parent_id=top_node.id,
                source="FACEBOOK",
            )
            appdb.session.add(facebook_node)
            appdb.session.commit()

        # TODO: ENCRYPT FILES

        print("Saving posts to database.")
        (
            total_posts,
            max_date,
            min_date,
            profile_updates,
            total_media,
        ) = posts_to_db(unzip_dir, facebook_node, current_user)

        # flash(
        #     f"Saved {str(total_posts)} posts between {min_date} and {max_date}. This includes {str(profile_updates)} profile updates. {str(total_media)} media files were uploaded.",
        #     "alert-success",
        # )
        upload_success = True

        # Add uploaded and parsed Facebook files to Filecoin
        print("Encrypting and uploading files to Filecoin")
        derived_user_key = derive_key_from_usercreds(
            current_user.username.encode("utf-8"), current_user.password.encode("utf-8")
        )
        # TODO: push dir to filecoin
        # push_dir_to_filecoin(unzip_dir, derived_user_key)

        # TODO: DELETE CACHED COPIES OF FILE UPLOADS

    # except (IsADirectoryError, zipfile.BadZipFile):
    # Return if the user did not provide a file to upload
    # TODO: Add flash output to facebook_upload template
    # flash(
    #     "Please make sure that you've selected a file and that it's in ZIP format.",
    #     "alert-danger",
    # )
    # except GRPCNotAvailableException:
    # flash(
    #     "Could not connect to Powergate Host.",
    #     "alert-danger",
    # )
    except Exception as e:
        tb = traceback.TracebackException.from_exception(e)
        print("".join(tb.format()))
        print(type(e))

        # flash(
        #     "An error occured while uploading the archive: " + str(e),
        #     "alert-danger",
        # )
