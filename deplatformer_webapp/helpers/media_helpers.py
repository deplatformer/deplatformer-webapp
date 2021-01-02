import json
import os
import re
import shutil
from datetime import datetime

import ffmpeg
from PIL import Image


def create_thumbnail(filepath, filename, media_type):

    osfilepath = get_filepath(filepath, filename)
    osfileoutpath=get_thumbnailpath(filepath, filename)

    if media_type == "IMAGE":
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

    elif media_type == "VIDEO":

        # https://mhsiddiqui.github.io/2018/02/09/Using-FFmpeg-to-create-video-thumbnails-in-Python/
        # https://github.com/kkroening/ffmpeg-python/blob/master/examples/README.md#generate-thumbnail-for-video
        # https://trac.ffmpeg.org/wiki/Create%20a%20thumbnail%20image%20every%20X%20seconds%20of%20the%20video

        ff = (
            ffmpeg
                .input(osfilepath)
                .filter('scale', "640", -1)
                .output(osfileoutpath, vframes=1)
        )

        print(ff)

        ff.run()

    return osfileoutpath


def get_thumbnailpath(filepath, filename):
    split = os.path.splitext(filename)
    thumbfilename = "".join([split[0], split[1], '.thumb', '.jpg'])

    osfileoutpath = os.path.join(filepath, thumbfilename)
    print("Image:  Thumbpath: %s" % thumbfilename)

    return osfileoutpath


def get_filepath(filepath, filename):
    print("Image:  Filepath: %s, %s" % (filepath, filename))
    osfilepath = os.path.join(filepath, filename)

    return osfilepath

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

