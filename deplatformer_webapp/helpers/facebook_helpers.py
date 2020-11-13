import json
import os
import shutil
import sqlite3
from datetime import datetime

import ftfy
from flask import app
from werkzeug.utils import secure_filename

from deplatformer_webapp.models.facebook import Media

from ..app import db as appdb
from ..models import facebook


def activate_hyperlinks(
    post,
):

    post_length = len(post)
    post_slice = post
    slice_length = post_length
    i = 0
    url_count = 0

    while i < post_length:
        url = ""
        http = post_slice.find("http")

        if http == -1:
            break

        for i in range(
            http,
            slice_length,
        ):
            url += post_slice[i]
            if i == slice_length - 1:
                break
            if post_slice[i + 1] == " ":
                break

        post = post.replace(
            url,
            "<a href='" + url + "'>" + url + "</a>",
        )
        url_count += 1

        post_slice = post_slice[
            slice(
                i + 1,
                post_length,
            )
        ]
        slice_length = len(post_slice)

    return (
        post,
        url_count,
    )


def cut_hyperlinks(
    post,
):

    post_length = len(post)
    post_slice = post
    slice_length = post_length
    i = 0
    urls = []
    while i < post_length:
        url = ""
        http = post_slice.find("http")

        if http == -1:
            break

        for i in range(
            http,
            slice_length,
        ):
            url += post_slice[i]
            if i == slice_length - 1:
                break
            if post_slice[i + 1] == " ":
                break

        post = post.replace(
            url,
            "",
        )
        urls.append(url)

        post_slice = post_slice[
            slice(
                i + 1,
                post_length,
            )
        ]
        slice_length = len(post_slice)

    return (
        post,
        urls,
    )


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


def posts_to_db(fb_dir, db_name):
    print("Parsing Facebook content.")
    db = sqlite3.connect(db_name)
    cursor = db.cursor()

    # Add albums with media files first so they can be referenced from posts
    albums_to_db(fb_dir)

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

                if timestamp is not None:
                    cursor.executemany(
                        "INSERT INTO posts (timestamp, post, url, url_label, place_name, address, latitude, longitude, profile_update) VALUES (?,?,?,?,?,?,?,?,?)",
                        [
                            (
                                timestamp,
                                post,
                                url,
                                url_label,
                                place_name,
                                address,
                                latitude,
                                longitude,
                                profile_update,
                            )
                        ],
                    )
                    db.commit()

                    # Get current post_id
                    cursor.execute("SELECT last_insert_rowid()")
                    post_id = cursor.fetchone()

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
                                    cursor.execute(
                                        "SELECT id FROM media where filepath=?",
                                        (filepath,),
                                    )
                                    media_file = cursor.fetchone()
                                    # Update media record with post_id
                                    cursor.execute(
                                        "UPDATE media SET post_id=? WHERE id=?",
                                        (
                                            post_id[0],
                                            media_file[0],
                                        ),
                                    )
                                    db.commit()

                                except Exception as e:
                                    print(str(post_id[0]) + ": media file not found")

                    # Count total number of media files for this post
                    cursor.execute(
                        "SELECT COUNT(id) FROM media WHERE post_id=?",
                        (int(post_id[0]),),
                    )
                    total_files = cursor.fetchone()
                    # Update post record with number of media files
                    cursor.execute(
                        "UPDATE posts SET media_files=? WHERE id=?",
                        (
                            total_files[0],
                            post_id[0],
                        ),
                    )
                    db.commit()

                except:
                    pass

    # Count total number of posts
    cursor.execute("SELECT COUNT(id) FROM posts")
    subtotal_posts = cursor.fetchone()

    print("Adding profile updates.")

    # Load FB profile update history
    f = open(os.path.join(fb_dir + "/profile_information/profile_update_history.json"))
    profile_updates = json.load(f)
    updates = profile_updates["profile_updates"]

    for update in updates:
        try:
            # Check whether the update is linked to a media file, if not, loop will continue
            filepath = update["attachments"][0]["data"][0]["media"]["uri"]
            cursor.execute(
                "SELECT id, post_id, timestamp, description FROM media where filepath=?",
                (filepath,),
            )
            media_file = cursor.fetchone()
            if media_file[0] == None:
                # Update is not linked to a media file
                continue
            if media_file[1] != None:
                # Media file is already linked to a post, we need to create a new media file stub later
                new_media = True
            else:
                new_media = False
            # Get profile update metadata
            try:
                unix_time = update["timestamp"]
                timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
            except:
                timestamp = None
            try:
                title = update["title"]
            except:
                title = None

            # Save profile update as post
            cursor.executemany(
                "INSERT INTO posts (timestamp, post, media_files, profile_update) VALUES (?,?,?,?)",
                [
                    (
                        timestamp,
                        title,
                        1,
                        True,
                    )
                ],
            )
            db.commit()

            # Get current post_id
            cursor.execute("SELECT last_insert_rowid()")
            post_id = cursor.fetchone()

            try:
                if new_media == False:
                    # Update existing media record with post_id
                    cursor.execute(
                        "UPDATE media SET post_id=? WHERE id=?",
                        (
                            post_id[0],
                            media_file[0],
                        ),
                    )
                else:
                    # Create new media record to link post to. Don't duplicate the album link.
                    cursor.execute(
                        "INSERT INTO media (timestamp, description, filepath, post_id) VALUES (?,?,?,?)",
                        (
                            media_file[2],
                            media_file[3],
                            filepath,
                            post_id[0],
                        ),
                    )
                db.commit()
            except Exception as e:
                print("couldn't update media file with post id")
                print(e)

        except:
            # Profile update does not have a media file attached, so don't include it
            continue

    # Recount total number of posts
    cursor.execute("SELECT COUNT(id) FROM posts")
    total_posts = cursor.fetchone()

    # Calculate total number of profile updates
    profile_updates = total_posts[0] - subtotal_posts[0]

    # Get latest post date
    cursor.execute("SELECT MAX(date(timestamp)) from posts")
    max_date = cursor.fetchone()

    # Get first post date
    cursor.execute("SELECT MIN(date(timestamp)) from posts")
    min_date = cursor.fetchone()

    # Count total number of media files
    cursor.execute("SELECT COUNT(id) FROM media")
    total_media = cursor.fetchone()

    return (
        total_posts,
        max_date,
        min_date,
        profile_updates,
        total_media,
    )


def albums_to_db(
    fb_dir,
    db_name,
):
    # FB includes one JSON file per album
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

            # Save album info
            album = facebook.Album(
                name=name, description=description, last_modified=last_modified, cover_photo_id=cover_photo
            )
            appdb.session.add(album)
            appdb.session.commit()

            for photo in album_contents["photos"]:
                filepath = photo.get("uri", None)
                if filepath is None or filepath[:18] != "photos_and_videos/":  # Don't inlude links to external images
                    continue

                unix_time = photo.get("creation_timestamp", None)
                timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S") if unix_time else None
                title = ftfy.fix_text(photo["title"]) if photo.get("title") else None
                description = ftfy.fix_text(photo["description"]) if photo.get("description") else None
                latitude = photo.get("media_metadata", {}).get("photo_metadata", {}).get("latitude", None)
                longitude = photo.get("media_metadata", {}).get("photo_metadata", {}).get("longitude", None)
                orientation = photo.get("media_metadata", {}).get("photo_metadata", {}).get("orientation", None)

                media = facebook.Media(
                    timestamp=timestamp,
                    title=title,
                    description=description,
                    latitude=latitude,
                    longitude=longitude,
                    orientation=orientation,
                    filepath=filepath,
                    post_id=None,
                    album_id=album.id,
                )
                appdb.session.add(media)
                appdb.session.commit()

            total_files = len(facebook.Media.query.filter_by(album_id=album.id).all())
            if total_files == 0:
                # Delete albums that have zero files
                appdb.session.delete(album)
                appdb.session.commit()
                continue

            # Get cover photo id for this album
            cover_photo = facebook.Media.query.filter_by(filepath=album_contents["cover_photo"]["uri"]).first()
            album.total_files = total_files
            album.cover_photo_id = cover_photo.id

            appdb.session.commit()

    # FB includes one directory of images that does not have a JSON file
    # Save 'your_posts' as an album
    if os.path.isdir(fb_dir + "/photos_and_videos/your_posts/"):
        album = facebook.Album(name="Your Posts")
        appdb.session.add(album)
        appdb.session.commit()

        files = os.listdir(fb_dir + "/photos_and_videos/your_posts/")
        for file in files:
            filepath = "photos_and_videos/your_posts/" + file
            media = facebook.Media(filepath=filepath, album_id=album.id)
            appdb.session.add(media)
            appdb.session.commit()

        # Count total number of photos for this album
        total_files = len(facebook.Media.query.filter_by(album_id=album.id).all())

        # Use the first photo as a cover for the album
        cover_photo = facebook.Media.query.filter_by(album_id=album.id).first()

        # Update album record with number of photos and cover photo
        album.total_files = total_files
        album.cover_photo = cover_photo.id
        appdb.session.commit()

    # Include the video directory
    if os.path.isdir(fb_dir + "/photos_and_videos/videos/"):
        album = facebook.Album(name="Videos")
        appdb.session.add(album)
        appdb.session.commit()

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

                media = facebook.Media(
                    timestamp=timestamp, description=description, filepath=filepath, album_id=album.id
                )
                appdb.session.add(media)
                appdb.session.commit()

        # Count total number of videos in this album
        total_files = len(facebook.Media.query.filter_by(album_id=album.id).all())

        # Use the first video as a cover for the album
        cover_video = facebook.Media.query.filter_by(album_id=album.id).first()

        # Update album record with number of videos and cover video
        album.total_files = total_files
        album.cover_photo = cover_video
        appdb.session.commit()


def create_user_dirs(user, base_path):
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
    facebook_dir = os.path.join(
        user_dir,
        "facebook",
    )
    if os.path.exists(facebook_dir):
        # Remove an existing directory to avoid dbase entry duplication
        shutil.rmtree(facebook_dir)
    os.makedirs(facebook_dir)
    return facebook_dir


def save_upload_file(upload_file, directory):
    file_name = secure_filename(upload_file.filename)
    print("Saving uploaded file")  # TODO: move to async user output
    upload_file.save(
        os.path.join(
            directory,
            file_name,
        )
    )
    return file_name
