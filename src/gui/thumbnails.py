#!/bin/python3

import os
from PIL import Image

import definitions.theme as themedef
from utils.theme import list_valid_themes, WallpaperTheme
from definitions.dirs import THEMES_DIR, ROOT_DIR, THUMBNAILS_DIR

THUMBNAIL_SIZE = (512, 288)
THUMBNAIL_CROP_BOX = (256, 0, 512, 288)


def generate_thumbnails():
    themes = list_valid_themes()
    for theme_abspath in [os.path.join(THEMES_DIR, theme) for theme in themes]:
        theme = WallpaperTheme()
        theme.open(theme_abspath)
        day_img_path = theme.filelist_day()[0]
        night_img_path = theme.filelist_night()[0]
        try:
            img_day = Image.open(day_img_path)
            img_night = Image.open(night_img_path)

            img_day.thumbnail(THUMBNAIL_SIZE)
            img_night.thumbnail(THUMBNAIL_SIZE)

            img_night = img_night.crop(THUMBNAIL_CROP_BOX)

            img_day.paste(img_night, THUMBNAIL_CROP_BOX)

            outfile = os.path.join(
                THUMBNAILS_DIR, f'{theme.title()}.jpg')

            if not os.path.exists(THUMBNAILS_DIR):
                os.makedirs(THUMBNAILS_DIR, exist_ok=True)

            img_day.save(outfile, "JPEG")
        except IOError:
            print("Cannot create thumbnail for:", outfile)
