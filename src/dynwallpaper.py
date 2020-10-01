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

# how long it takes to get actually dark after sunset (in seconds)
# rough average approximation based on nautical twilight for latitudes between 0 to 70 degrees (N/S)
TWILIGHT_DURATION = 3600

# ---------------- Dynamic Wallpaper class --------------------


class DynWallpaper:
    def __init__(self):
        self.__latitude, self.__longitude = DEFAULT_GEOLOCATION
        self.__timezone = local_tzoffset()
        self.__theme = WallpaperTheme()
        self.__sunrise, self.__snoon, self.__sunset = soltime.timetuple(
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
        self.__sunrise, self.__snoon, self.__sunset = soltime.timetuple(
            self.__latitude, self.__longitude, self.__timezone)

    def set_theme(self, theme_dirpath: str) -> bool:
        return self.__theme.open(theme_dirpath)

    def set_timezone_host(self):
        self.__timezone = local_tzoffset()

    def set_timezone(self, timezone: float):
        self.__timezone = timezone

    def __calculate_timings(self, transition_time: int) -> dict:
        from itertools import repeat
        timings = dict(zip(themedef.DAYTIMES, repeat([])))
        sunrise_dur = self.__snoon - self.__sunrise
        noon_dur = NOON_DURATION
        day_dur = (self.__sunset - self.__snoon -
                   noon_dur) * DAY_SUNSET_RATIO
        sunset_dur = (self.__sunset - self.__snoon -
                      noon_dur) - day_dur + TWILIGHT_DURATION
        night_dur = DAY_LENGTH - sunrise_dur - noon_dur - day_dur - sunset_dur

        if len(self.__theme.filelist_sunrise()) == 0:
            day_dur += sunrise_dur
            sunrise_dur = 0

        if len(self.__theme.filelist_noon()) == 0:
            day_dur += noon_dur
            noon_dur = 0

        if len(self.__theme.filelist_sunset()) == 0:
            day_dur += sunset_dur
            sunset_dur = 0

        durations = [sunrise_dur, noon_dur, day_dur, sunset_dur, night_dur]
        daytime_files = self.__theme.filelist_all()

        for i, daytime in enumerate(themedef.DAYTIMES):
            if durations[i] == 0:
                timings[daytime] = []
                continue

            trans_time = transition_time
            if trans_time * len(daytime_files[daytime]) >= durations[i]:
                print(
                    f'WARNING: Transitions take longer than duration of {daytime}! Fixing timings...')
                trans_time = (
                    durations[i] - len(daytime_files[daytime])) // len(daytime_files[daytime])

            sub_dur = durations[i] - trans_time * len(daytime_files[daytime])
            static_dur = [sub_dur // len(daytime_files[daytime])
                          for _ in range(len(daytime_files[daytime]))]

            # fix static time
            if sum(static_dur) != sub_dur:
                static_dur.append(sub_dur - sum(static_dur) + static_dur.pop())

            timings[daytime] = [(x, trans_time) for x in static_dur]

        validation_sum = sum(flatten(flatten(timings.values())))
        if validation_sum != DAY_LENGTH:
            raise Exception(
                f"Total animation length does not equal 24 hours! It is: {validation_sum}, should be {DAY_LENGTH}")

        return timings

    def generate_xml(self, transition_time=600) -> str:
        opt_sett = self.__theme.optional_settings()
        if themedef.OPT_PREF_TRANSITION_DURATION in opt_sett:
            transition_time = opt_sett[themedef.OPT_PREF_TRANSITION_DURATION]
        timings = self.__calculate_timings(transition_time)

        root = Et.Element("background")
        start_time = Et.SubElement(root, "starttime")

        Et.SubElement(start_time, "year").text = "2020"
        Et.SubElement(start_time, "month").text = "1"
        Et.SubElement(start_time, "day").text = "1"
        Et.SubElement(start_time, "hour").text = f"{self.__sunrise // 3600}"
        Et.SubElement(
            start_time, "minute").text = f"{(self.__sunrise % 3600) // 60}"
        Et.SubElement(start_time, "second").text = "0"

        daytime_files = self.__theme.filelist_all()

        for count, daytime in enumerate(themedef.DAYTIMES):
            for index, wallpaper in enumerate(daytime_files[daytime]):
                # static background
                tmp = Et.SubElement(root, "static")

                Et.SubElement(tmp, "file").text = wallpaper
                Et.SubElement(tmp, "duration").text = str(
                    timings[daytime][index][0])

                # transition to next background
                tmp = Et.SubElement(root, "transition", type="overlay")
                Et.SubElement(tmp, "duration").text = str(
                    timings[daytime][index][1])
                Et.SubElement(tmp, "from").text = wallpaper

                if index + 1 >= len(daytime_files[daytime]):
                    next_daytime_wallpapers = []
                    while len(next_daytime_wallpapers) == 0:
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

        xml_path = f'{WALLPAPER_XML_DIR}/{NAME}-{int(datetime.now().timestamp())}.xml'

        if os.path.exists(WALLPAPER_XML_DIR):
            clear_wallpaper_xml_dir()
        else:
            os.mkdir(WALLPAPER_XML_DIR)

        with open(xml_path, 'w') as f:
            f.write(
                f'<!-- Generated by {NAME} {VERSION} by {AUTHOR} -->\n')
            f.write(
                f'<!-- {GITHUB} -->\n')
            f.write(xml_str)
        return xml_path

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
