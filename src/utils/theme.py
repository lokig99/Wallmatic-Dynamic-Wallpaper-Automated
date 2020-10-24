#!/bin/python3

import json
import os

from definitions.dirs import THEMES_DIR
import definitions.theme as themedef

THEME_FILE = "theme.json"


def validate_theme_dir(theme_dirpath: str) -> bool:
    return os.path.isdir(theme_dirpath) and THEME_FILE in os.listdir(theme_dirpath)


def list_valid_themes() -> list:
    themes_list = []
    for d in os.listdir(THEMES_DIR):
        d_abspath = os.path.join(THEMES_DIR, d)
        if validate_theme_dir(d_abspath):
            themes_list.append(d)
    return themes_list


def select_theme() -> str:
    themes = sorted(list_valid_themes())
    if len(themes) == 0:
        raise Exception(f'No themes available in {THEMES_DIR}')

    print('Available wallpaper themes:\n')
    for i, theme in enumerate(themes):
        print(f'[{i}]\t{theme.replace("_", " ")}')
    choice = input('\nselect theme (eg: 1, default=0): ')
    if not choice.isdigit() or int(choice) >= len(themes):
        choice_int = 0
    else:
        choice_int = int(choice)
    return os.path.join(THEMES_DIR, themes[choice_int])


class WallpaperTheme:
    def __init__(self):
        self.__theme_abspath = ''
        self.__themedict = {}
        self.__img_path_template = ''
        self.__opened = False

    def open(self, theme_dirpath: str) -> bool:
        theme_dirpath = os.path.abspath(theme_dirpath)

        if validate_theme_dir(theme_dirpath):
            theme_json_path = os.path.join(theme_dirpath, THEME_FILE)
            try:
                with open(theme_json_path, 'r') as f:
                    theme = json.load(f)
                self.__opened = True
                self.__theme_abspath = theme_dirpath
                self.__themedict = theme
                self.__img_path_template = os.path.join(
                    theme_dirpath, theme[themedef.FILENAME])
                return True
            except IOError:
                print("Could not read file: ", theme_json_path)
            except json.JSONDecodeError:
                print("Error occurred while trying to parse JSON file: ",
                      theme_json_path)

        self.__opened = False
        self.__theme_abspath = ''
        self.__themedict = {}
        self.__img_path_template = ''
        return False

    def ready(self) -> bool:
        return self.__opened

    def title(self) -> str:
        if self.ready():
            return self.__themedict[themedef.TITLE]

        return ""

    def credits(self) -> str:
        if self.ready():
            return self.__themedict[themedef.CREDITS]
        return ""

    def description(self) -> str:
        if self.ready():
            return self.__themedict[themedef.DESCRIPTION]
        return ""

    def filelist_sunrise(self) -> list:
        if self.ready():
            return [self.__img_path_template.replace('*', str(x)) for x in self.__themedict[themedef.FILE_LIST][themedef.FL_SUNRISE]]
        return []

    def filelist_noon(self) -> list:
        if self.ready():
            return [self.__img_path_template.replace('*', str(x)) for x in self.__themedict[themedef.FILE_LIST][themedef.FL_NOON]]
        return []

    def filelist_day(self) -> list:
        if self.ready():
            return [self.__img_path_template.replace('*', str(x)) for x in self.__themedict[themedef.FILE_LIST][themedef.FL_DAY]]
        return []

    def filelist_sunset(self) -> list:
        if self.ready():
            return [self.__img_path_template.replace('*', str(x)) for x in self.__themedict[themedef.FILE_LIST][themedef.FL_SUNSET]]
        return []

    def filelist_night(self) -> list:
        if self.ready():
            return [self.__img_path_template.replace('*', str(x)) for x in self.__themedict[themedef.FILE_LIST][themedef.FL_NIGHT]]
        return []

    def filelist_all(self) -> dict:
        if self.ready():
            files_tuple = self.filelist_sunrise(), self.filelist_noon(
            ), self.filelist_day(), self.filelist_sunset(), self.filelist_night()
            return dict(zip(themedef.DAYTIMES, files_tuple))
        return {}

    def optional_settings(self) -> dict:
        if self.ready() and themedef.OPTIONAL_SETTINGS in self.__themedict:
            return self.__themedict[themedef.OPTIONAL_SETTINGS]
        return {}
