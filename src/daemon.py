#!/bin/python3

import time
import subprocess
from datetime import datetime, timedelta

import utils.localization as loc
import utils.solartime as soltime
from utils.misc import local_tzoffset
from utils.gnome_theming import change_cursor_theme, change_gtk_theme, change_shell_theme

INTERVAL_SEC = 1


def in_timeframe(start: datetime, end: datetime) -> bool:
    now = datetime.now()
    return now >= start and now < end


def get_lightmode_timeframe(lat: float, lon: float) -> tuple:
    tz_offset = local_tzoffset()
    now = datetime.now()

    sunrise_dt = soltime.get_sunrise_datetime(
        lat, lon, now, tz_offset) + timedelta(minutes=90)
    evening_dt = soltime.get_sunset_datetime(
        lat, lon, now, tz_offset) - timedelta(minutes=90)

    return sunrise_dt, evening_dt


def loop():
    def current_date() -> tuple:
        dt_timetuple = datetime.now().timetuple()
        return dt_timetuple.tm_year, dt_timetuple.tm_yday

    def change_theme_on_timeframe(start: datetime, end: datetime, is_darkmode: bool, force_refresh=False) -> bool:
        if in_timeframe(start, end):
            if is_darkmode or force_refresh:
                change_gtk_theme('Pop')
                change_shell_theme('Pop')
                change_cursor_theme('xcursor-breeze-snow')
                is_darkmode = False
        elif not is_darkmode:
            change_gtk_theme('Pop-dark')
            change_shell_theme('Pop-dark')
            change_cursor_theme('xcursor-breeze')
            is_darkmode = True
        return is_darkmode

    prev_date = current_date()
    lat, lon = loc.get_geolocation()
    start, end = get_lightmode_timeframe(lat, lon)
    is_darkmode = change_theme_on_timeframe(
        start, end, is_darkmode=False, force_refresh=True)

    while True:
        cur_date = current_date()
        if prev_date != cur_date:
            start, end = get_lightmode_timeframe(lat, lon)
            prev_date = cur_date

        is_darkmode = change_theme_on_timeframe(start, end, is_darkmode)

        time.sleep(INTERVAL_SEC)