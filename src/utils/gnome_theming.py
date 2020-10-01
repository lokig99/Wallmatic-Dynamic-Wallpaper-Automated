#!/bin/python3

import os
import re
import subprocess
from itertools import repeat

SYSTEM_WINDOW_THEMES = '/usr/share/themes'
SYSTEM_ICON_THEMES = '/usr/share/icons'
USER_WINDOW_THEMES = os.path.expanduser('~/.themes')
USER_ICON_THEMES = os.path.expanduser('~/.icons')

INDEX_THEME = 'index.theme'
ICON_DIRS = set(('8x8', '16x16', '32x32', '64x64',
                 '128x128', '256x256', '512x512', 'scalable'))
SHELL_DIR = 'gnome-shell'
CURSOR_DIR = 'cursors'


def convert_to_simple_string(text: str) -> str:
    return re.compile(r'[^a-zA-Z0-9_-]+', re.UNICODE).sub('', text)


def get_gtk_theme() -> str:
    cmd = 'gsettings get org.gnome.desktop.interface gtk-theme'
    theme, err = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True).communicate()
    if err == '':
        return convert_to_simple_string(theme)
    return ''


def get_shell_theme() -> str:
    cmd = 'gsettings get org.gnome.shell.extensions.user-theme name'
    theme, err = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True).communicate()
    if err == '':
        return convert_to_simple_string(theme)
    return ''


def get_wallpaper() -> str:
    cmd = 'gsettings get org.gnome.desktop.background picture-uri'
    wallpaper, err = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True).communicate()
    if err == '':
        return wallpaper
    return ''


def change_gtk_theme(theme_name: str):
    subprocess.call(
        f'gsettings set org.gnome.desktop.interface gtk-theme {theme_name}', shell=True)


def change_cursor_theme(theme_name: str):
    subprocess.call(
        f'gsettings set org.gnome.desktop.interface cursor-theme {theme_name}', shell=True)


def change_shell_theme(theme_name: str):
    subprocess.call(
        f'gsettings set org.gnome.shell.extensions.user-theme name {theme_name}', shell=True)


def get_themes(dirpath: str) -> list:
    try:
        themes_dirs_abs = list(
            map(os.path.join, repeat(dirpath), os.listdir(dirpath)))
        themes_dirs_abs = [d for d in themes_dirs_abs if os.path.isdir(
            d) and INDEX_THEME in os.listdir(d)]

        themes_dirs_base = list(map(os.path.basename, themes_dirs_abs))
    except:
        themes_dirs_abs = []
        themes_dirs_base = []
        print(f'Error reading {dirpath}')
    finally:
        return list(zip(themes_dirs_base, themes_dirs_abs))


def list_gtk_themes() -> list:
    return get_themes(SYSTEM_WINDOW_THEMES) + get_themes(USER_WINDOW_THEMES)


def list_shell_themes() -> list:
    return [t for t in list_gtk_themes() if SHELL_DIR in os.listdir(t[1])]


def list_icon_themes() -> list:
    themes = get_themes(SYSTEM_ICON_THEMES) + get_themes(USER_ICON_THEMES)
    return [t for t in themes if not ICON_DIRS.isdisjoint(os.listdir(t[1]))]


def list_cursor_themes() -> list:
    themes = get_themes(SYSTEM_ICON_THEMES) + get_themes(USER_ICON_THEMES)
    return [t for t in themes if CURSOR_DIR in os.listdir(t[1])]
