import json
import os
import sqlite3
from datetime import datetime

import ftfy


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


def posts_to_db(
    fb_dir,
):
    # Get FB content directory name, use as database name & location
    db_name = os.path.basename(os.path.normpath(fb_dir))
    # Create database if it doesn't exist
    db = sqlite3.connect(fb_dir + "/" + db_name + ".sqlite")
    cursor = db.cursor()
    # Create database structure if it doesn't exist
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS posts(id INTEGER NOT NULL PRIMARY KEY, timestamp TEXT, post TEXT, media_files INTEGER, url TEXT, url_label TEXT, place_name TEXT, address TEXT, latitude TEXT, longitude TEXT, profile_update BOOLEAN)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS media(id INTEGER NOT NULL PRIMARY KEY, timestamp TEXT, title TEXT, description TEXT, latitude TEXT, longitude TEXT, orientation INTEGER, filepath TEXT, post_id INTEGER, album_id INTEGER, FOREIGN KEY(post_id) REFERENCES posts(id), FOREIGN KEY(album_id) REFERENCES albums(id))"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS filepath ON media(filepath)")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS albums(id INTEGER NOT NULL PRIMARY KEY, last_modified TEXT, name TEXT, description TEXT, total_files INTEGER, cover_photo_id INTEGER, FOREIGN KEY(cover_photo_id) REFERENCES media(id))"
    )
    cursor.execute("CREATE TABLE IF NOT EXISTS tags(id INTEGER NOT NULL PRIMARY KEY, tag TEXT)")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS tag_links(id INTEGER NOT NULL PRIMARY KEY, tag_id INTEGER, post_id INTEGER, FOREIGN KEY(tag_id) REFERENCES tags(id), FOREIGN KEY (post_id) REFERENCES posts(id))"
    )
    db.commit()

    # Add albums with media files first so they can be referenced from posts
    albums_to_db(
        fb_dir,
        db_name,
    )

    # FB might include more than one posts JSON file
    files = os.listdir(fb_dir + "/posts/")
    for file in files:
        file_split = os.path.splitext(file)
        if (file_split[0][:10] == "your_posts") and (file_split[1] == ".json"):
            # Read data from FB JSON file
            f = open(os.path.join(fb_dir + "/posts/" + file))
            posts = json.load(f)

            for content in posts:
                unix_time = content["timestamp"]
                timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")

                try:
                    post_source = content["data"][0]["post"]
                    # Clean up FB's garbage UTF-8 (Mojibake)
                    post = ftfy.fix_text(post_source)
                except:
                    try:
                        post = content["title"]
                    except:
                        post = None

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
    # intiliaze database
    db = sqlite3.connect(fb_dir + "/" + db_name + ".sqlite")
    cursor = db.cursor()

    # FB includes one JSON file per album
    files = os.listdir(fb_dir + "/photos_and_videos/album/")
    for file in files:
        file_split = os.path.splitext(file)
        if file_split[1] == ".json":
            # Read data from FB JSON file
            f = open(os.path.join(fb_dir + "/photos_and_videos/album/" + file))
            album = json.load(f)
            try:
                unix_time = album["last_modified_timestamp"]
                last_modified = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
            except:
                last_modified = None
            try:
                description = album["description"]
            except:
                description = None
            try:
                name = album["name"]
            except:
                name = None
            cover_photo = None  # get Media file id to use as foreign key
            # Save album info
            cursor.executemany(
                "INSERT INTO albums (last_modified, name, description, cover_photo_id) VALUES (?,?,?,?)",
                [
                    (
                        last_modified,
                        name,
                        description,
                        cover_photo,
                    )
                ],
            )
            db.commit()

            # Get current album_id
            cursor.execute("SELECT last_insert_rowid()")
            album_id = cursor.fetchone()

            for photo in album["photos"]:
                try:
                    filepath = photo["uri"]
                except:
                    # Photo does not exist
                    continue
                if filepath[:18] != "photos_and_videos/":
                    # Don't inlude links to external images
                    continue
                try:
                    unix_time = photo["creation_timestamp"]
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    timestamp = None
                try:
                    title = ftfy.fix_text(photo["title"])
                except:
                    title = None
                try:
                    description = ftfy.fix_text(photo["description"])
                except:
                    description = None
                try:
                    latitude = photo["media_metadata"]["photo_metadata"]["latitude"]
                except:
                    latitude = None
                try:
                    longitude = photo["media_metadata"]["photo_metadata"]["longitude"]
                except:
                    longitude = None
                try:
                    orientation = photo["media_metadata"]["photo_metadata"]["orientation"]
                except:
                    orientation = None

                cursor.executemany(
                    "INSERT INTO media (timestamp, title, description, latitude, longitude, orientation, filepath, post_id, album_id) VALUES (?,?,?,?,?,?,?,?,?)",
                    [
                        (
                            timestamp,
                            title,
                            description,
                            latitude,
                            longitude,
                            orientation,
                            filepath,
                            None,
                            album_id[0],
                        )
                    ],
                )
                db.commit()

            # Count total number of photos for this album
            cursor.execute(
                "SELECT COUNT(id) FROM media WHERE album_id=?",
                (album_id[0],),
            )
            total_files = cursor.fetchone()
            if (total_files[0] == None) or (total_files[0] == 0):
                # Delete albums that have zero files
                cursor.execute(
                    "DELETE FROM albums WHERE id=?",
                    (album_id[0],),
                )
                db.commit
                continue
            # Get cover photo id for this album
            cursor.execute(
                "SELECT id FROM media where filepath=?",
                (album["cover_photo"]["uri"],),
            )
            cover_photo = cursor.fetchone()
            try:
                cover_photo_id = cover_photo[0]
            except:
                cover_photo_id = None
            # Update album record with number of photos and cover_photo_id
            cursor.execute(
                "UPDATE albums SET total_files=?, cover_photo_id=? WHERE id=?",
                (
                    total_files[0],
                    cover_photo_id,
                    album_id[0],
                ),
            )
            db.commit()

    # FB includes one directory of images that does not have a JSON file
    # Save 'your_posts' as an album
    if os.path.isdir(fb_dir + "/photos_and_videos/your_posts/"):
        cursor.execute(
            "INSERT INTO albums (name) VALUES (?)",
            ("Your Posts",),
        )
        db.commit()

        # Get album_id
        cursor.execute("SELECT last_insert_rowid()")
        album_id = cursor.fetchone()

        files = os.listdir(fb_dir + "/photos_and_videos/your_posts/")
        for file in files:
            filepath = "photos_and_videos/your_posts/" + file
            cursor.executemany(
                "INSERT INTO media (filepath, album_id) VALUES (?,?)",
                [
                    (
                        filepath,
                        album_id[0],
                    )
                ],
            )
            db.commit()

        # Count total number of photos for this album
        cursor.execute(
            "SELECT COUNT(id) FROM media WHERE album_id=?",
            (album_id[0],),
        )
        total_files = cursor.fetchone()

        # Use the first photo as a cover for the album
        cursor.execute(
            "SELECT id FROM media WHERE album_id=?",
            (album_id[0],),
        )
        cover_photo = cursor.fetchone()

        # Update album record with number of photos and cover photo
        cursor.execute(
            "UPDATE albums SET total_files=?, cover_photo_id=? WHERE id=?",
            (
                total_files[0],
                cover_photo[0],
                album_id[0],
            ),
        )
        db.commit()

    # Include the video directory
    if os.path.isdir(fb_dir + "/photos_and_videos/videos/"):
        cursor.execute(
            "INSERT INTO albums (name) VALUES (?)",
            ("Videos",),
        )
        db.commit()

        # Get album_id
        cursor.execute("SELECT last_insert_rowid()")
        album_id = cursor.fetchone()

        if os.path.isfile(fb_dir + "/photos_and_videos/your_videos.json"):
            f = open(fb_dir + "/photos_and_videos/your_videos.json")
            videos = json.load(f)
            for video in videos["videos"]:
                try:
                    filepath = video["uri"]
                except:
                    # Video file does not exist
                    continue
                if filepath[:18] != "photos_and_videos/":
                    # Don't inlude links to external videos
                    continue
                try:
                    unix_time = video["creation_timestamp"]
                    timestamp = datetime.fromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    timestamp = None
                try:
                    description = video["description"]
                except:
                    description = None
                cursor.executemany(
                    "INSERT INTO media (timestamp, description, filepath, album_id) VALUES (?,?,?,?)",
                    [
                        (
                            timestamp,
                            description,
                            filepath,
                            album_id[0],
                        )
                    ],
                )
                db.commit()

        # Count total number of videos in this album
        cursor.execute(
            "SELECT COUNT(id) FROM media WHERE album_id=?",
            (album_id[0],),
        )
        total_files = cursor.fetchone()

        # Use the first video as a cover for the album
        cursor.execute(
            "SELECT id FROM media WHERE album_id=?",
            (album_id[0],),
        )
        cover_video = cursor.fetchone()

        # Update album record with number of videos and cover video
        cursor.execute(
            "UPDATE albums SET total_files=?, cover_photo_id=? WHERE id=?",
            (
                total_files[0],
                cover_video[0],
                album_id[0],
            ),
        )
        db.commit()

    return ()
