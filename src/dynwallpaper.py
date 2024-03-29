#!/bin/python3

import os
import json
import subprocess
import xml.dom.minidom as dom
import xml.etree.ElementTree as Et
from datetime import datetime

import utils.localization as loc
import utils.solartime as soltime
import definitions.theme as themedef
from utils.theme import WallpaperTheme
from utils.misc import flatten, local_tzoffset
from definitions.dirs import WALLPAPER_XML_DIR, THEMES_DIR
from definitions.version import VERSION, AUTHOR, NAME, GITHUB

DEFAULT_GEOLOCATION = (0, 0)
DAY_LENGTH = 24 * 3600  # 24 hours (in seconds)
DAY_SUNSET_RATIO = 2 / 3

# total noon duration (in seconds) including transition to daytime wallpaper
NOON_DURATION = 1800

NIGHTMODE = "NightMode"

# ---------------- Dynamic Wallpaper class --------------------


class DynWallpaper:
    def __init__(self):
        self.__latitude, self.__longitude = DEFAULT_GEOLOCATION
        self.__timezone = local_tzoffset()
        self.__theme = WallpaperTheme()
        self.__sunrise, self.__snoon, self.__sunset, self.__twilight = soltime.timetuple(
            self.__latitude, self.__longitude, self.__timezone)

    def set_geolocation_online(self):
        try:
            self.__latitude, self.__longitude = loc.get_geolocation()
            return True
        except loc.EX_RequestTimeout as e:
            print(
                e, f"Setting fallback default geolocation: {DEFAULT_GEOLOCATION}", sep="\n")
            self.__latitude, self.__longitude = DEFAULT_GEOLOCATION
        return False

    def set_geolocation_manually(self, latitude: float, longitude: float):
        self.__latitude, self.__longitude = latitude, longitude

    def update_soltime(self):
        self.__sunrise, self.__snoon, self.__sunset, self.__twilight = soltime.timetuple(
            self.__latitude, self.__longitude, self.__timezone)

    def set_theme(self, theme_dirpath: str) -> bool:
        return self.__theme.open(theme_dirpath)

    def set_timezone_host(self):
        self.__timezone = local_tzoffset()

    def set_timezone(self, timezone: float):
        self.__timezone = timezone

    def __calculate_timings(self, transition_time: int, nightmode=False) -> dict:
        from itertools import repeat
        timings = dict(zip(themedef.DAYTIMES, repeat([])))
        sunrise_dur = self.__snoon - self.__sunrise
        noon_dur = NOON_DURATION
        twilight_dur = (self.__twilight - self.__sunset)
        day_dur = (self.__sunset - self.__snoon -
                   noon_dur) * DAY_SUNSET_RATIO
        sunset_dur = (self.__sunset - self.__snoon -
                      noon_dur) - day_dur + twilight_dur
        night_dur = DAY_LENGTH - sunrise_dur - noon_dur - day_dur - sunset_dur

        if not self.__theme.filelist_sunrise() or nightmode:
            day_dur += sunrise_dur
            sunrise_dur = 0

        if not self.__theme.filelist_noon() or nightmode:
            day_dur += noon_dur
            noon_dur = 0

        if not self.__theme.filelist_sunset() or nightmode:
            day_dur += sunset_dur
            sunset_dur = 0

        if nightmode:
            day_dur += night_dur
            night_dur = 0

        durations = [sunrise_dur, noon_dur, day_dur, sunset_dur, night_dur]

        if nightmode:
            daytime_files_amounts = dict([(d, 0) for d in themedef.DAYTIMES])
            daytime_files_amounts[themedef.FL_DAY] = len(
                self.__theme.filelist_night())
        else:
            daytime_files = self.__theme.filelist_all()
            daytime_files_amounts = dict(
                [(d, len(daytime_files[d])) for d in daytime_files])

        for i, daytime in enumerate(themedef.DAYTIMES):
            if durations[i] == 0:
                timings[daytime] = []
                continue

            trans_time = transition_time
            if trans_time * daytime_files_amounts[daytime] >= durations[i]:
                print(
                    f'WARNING: Transitions take longer than duration of {daytime}! Fixing timings...')
                trans_time = (
                    durations[i] - daytime_files_amounts[daytime]) // daytime_files_amounts[daytime]

            sub_dur = durations[i] - trans_time * \
                daytime_files_amounts[daytime]
            static_dur = [sub_dur // daytime_files_amounts[daytime]
                          for _ in range(daytime_files_amounts[daytime])]

            # fix static time
            if sum(static_dur) != sub_dur:
                static_dur.append(sub_dur - sum(static_dur) + static_dur.pop())

            timings[daytime] = [(x, trans_time) for x in static_dur]

        validation_sum = sum(flatten(flatten(timings.values())))
        if validation_sum != DAY_LENGTH:
            raise Exception(
                f"Total animation length does not equal 24 hours! It is: {validation_sum}, should be {DAY_LENGTH}")

        return timings

    def __generate_xml_string(self, daytime_files: dict, timings: dict, disable_transitions=False) -> str:
        root = Et.Element("background")
        start_time = Et.SubElement(root, "starttime")

        Et.SubElement(start_time, "year").text = "2020"
        Et.SubElement(start_time, "month").text = "1"
        Et.SubElement(start_time, "day").text = "1"
        Et.SubElement(start_time, "hour").text = f"{self.__sunrise // 3600}"
        Et.SubElement(
            start_time, "minute").text = f"{(self.__sunrise % 3600) // 60}"
        Et.SubElement(start_time, "second").text = "0"

        for count, daytime in enumerate(themedef.DAYTIMES):
            for index, wallpaper in enumerate(daytime_files[daytime]):
                # static background
                tmp = Et.SubElement(root, "static")

                Et.SubElement(tmp, "file").text = wallpaper
                Et.SubElement(tmp, "duration").text = str(
                    timings[daytime][index][0])

                # transition to next background
                if not disable_transitions:
                    tmp = Et.SubElement(root, "transition", type="overlay")
                    Et.SubElement(tmp, "duration").text = str(
                        timings[daytime][index][1])
                    Et.SubElement(tmp, "from").text = wallpaper

                    if index + 1 >= len(daytime_files[daytime]):
                        next_daytime_wallpapers = []
                        while not next_daytime_wallpapers:
                            count += 1
                            next_daytime_wallpapers = daytime_files[themedef.DAYTIMES[count % len(
                                themedef.DAYTIMES)]]
                        next_wallpaper = next_daytime_wallpapers[0]
                    else:
                        next_wallpaper = daytime_files[daytime][index + 1]

                    Et.SubElement(tmp, "to").text = next_wallpaper

        xml_header = dom.Document().toxml()
        xml_str = dom.parseString(Et.tostring(root)).toprettyxml(
            indent="   ")[len(xml_header) + 1:]

        return xml_str

    def __create_xml_file(self, xml_string: str, xml_filename: str) -> str:
        try:
            xml_path = os.path.join(WALLPAPER_XML_DIR, xml_filename)

            with open(xml_path, 'w') as f:
                f.write(
                    f'<!-- Generated by {NAME} {VERSION} by {AUTHOR} -->\n')
                f.write(
                    f'<!-- {GITHUB} -->\n')
                f.write(xml_string)

            return xml_path
        except:
            print(f"Failed to create file: {xml_path}")

        return ""

    def create_wallpaper_xml_files(self, transition_time=600) -> tuple:
        opt_sett = self.__theme.optional_settings()
        if themedef.OPT_PREF_TRANSITION_DURATION in opt_sett:
            transition_time = opt_sett[themedef.OPT_PREF_TRANSITION_DURATION]
        timestamp = int(datetime.now().timestamp())

        # standard wallpaper theme
        timings_standard = self.__calculate_timings(transition_time)
        xml_standard = self.__generate_xml_string(
            self.__theme.filelist_all(), timings_standard)
        xml_standard_name = f'{NAME}-{timestamp}.xml'

        # night mode wallpaper theme
        daytimes_nightmode = dict([(d, []) for d in themedef.DAYTIMES])
        daytimes_nightmode[themedef.FL_DAY] = self.__theme.filelist_night()

        if len(self.__theme.filelist_night()) == 1:
            timings_nightmode = self.__calculate_timings(0, nightmode=True)
            xml_nightmode = self.__generate_xml_string(
                daytimes_nightmode, timings_nightmode, disable_transitions=True)
        else:
            timings_nightmode = self.__calculate_timings(
                transition_time, nightmode=True)
            xml_nightmode = self.__generate_xml_string(
                daytimes_nightmode, timings_nightmode)

        xml_nightmode_name = f'{NAME}-{NIGHTMODE}-{timestamp}.xml'

        if os.path.exists(WALLPAPER_XML_DIR):
            clear_wallpaper_xml_dir()
        else:
            os.mkdir(WALLPAPER_XML_DIR)

        # save themes to files
        xml_nightmode_path = self.__create_xml_file(
            xml_nightmode, xml_nightmode_name)
        xml_standard_path = self.__create_xml_file(
            xml_standard, xml_standard_name)

        return xml_standard_path, xml_nightmode_path

    def theme_wallpaper_ontime(self, date: datetime) -> str:
        timings = self.__calculate_timings(0)
        day_sec = (date - datetime(date.year, date.month, date.day)
                   ).total_seconds()
        index = -1

        if day_sec >= self.__sunrise:
            tmp = self.__sunrise
            for count, timing in enumerate(flatten(timings.values())):
                tmp += timing[0]
                if day_sec <= tmp:
                    index = count
                    break

        return flatten(self.__theme.filelist_all().values())[index]

    def get_data_summary(self):
        return {'lat': self.__latitude, 'lon': self.__longitude, 'timezone': self.__timezone, 'sunrise': self.__sunrise,
                'snoon': self.__snoon, 'sunset': self.__sunset, 'theme': self.__theme.title()}


# ----------------------- Other --------------------------------

def clear_wallpaper_xml_dir():
    if os.path.exists(WALLPAPER_XML_DIR):
        files = [os.path.join(WALLPAPER_XML_DIR, f)
                 for f in os.listdir(WALLPAPER_XML_DIR)]
        xml_files = [f for f in files if f.lower().endswith('.xml')]

        for xmlf in xml_files:
            try:
                os.remove(xmlf)
            except OSError as e:
                print(f'Error: {xmlf}, {e.strerror}')
