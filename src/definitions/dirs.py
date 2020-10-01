#!/bin/python3
import os.path

__DEFINITIONS_DIR__ = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(__DEFINITIONS_DIR__)
ROOT_DIR = os.path.dirname(SRC_DIR)
THEMES_DIR = os.path.join(ROOT_DIR, 'themes')
WALLPAPER_XML_DIR = os.path.join(ROOT_DIR, 'wallpaper-xml')
ICONS_DIR = os.path.join(ROOT_DIR, 'icons')
CACHE_DIR = os.path.join(ROOT_DIR, 'cache')
THUMBNAILS_DIR = os.path.join(CACHE_DIR, 'thumbnails')

if __name__ == "__main__":
    print(__DEFINITIONS_DIR__, SRC_DIR, ROOT_DIR,
          THEMES_DIR, ICONS_DIR, WALLPAPER_XML_DIR, CACHE_DIR, THUMBNAILS_DIR, sep='\n')
