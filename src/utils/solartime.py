#!/bin/python3

from datetime import datetime, timedelta
from math import pi, cos, sin, acos, radians, tan

"""
General sun position calculations based on NOAA Global Monitoring Division data
for more information see: https://www.esrl.noaa.gov/gmd/grad/solcalc/solareqns.PDF
"""

SUNRISE_SUNSET_ZENITH = 90.0  # degrees
CIVIL_TWILIGHT_ZENITH = 96.0  # degrees


def cos_dg(degrees):
    return cos(radians(degrees))


def acos_dg(x):
    return acos(x) * (180 / pi)


def tan_dg(degrees):
    return tan(radians(degrees))


def fractional_year(date=datetime.now()):
    return (2 * pi) / 365 * (date.timetuple().tm_yday -
                             1 + (date.hour - 12) / 24)


def eq_time(f_year=fractional_year()):
    return 229.18 * (0.000075 + 0.001868 * cos(f_year) - 0.032077 * sin(
        f_year) - 0.014615 * cos(2 * f_year) - 0.040849 * sin(2 * f_year))


def sol_declination(f_year=fractional_year()):
    return 0.006918 - 0.399912 * cos(f_year) + 0.070257 * sin(f_year) - 0.006758 * cos(
        2 * f_year) + 0.000907 * sin(2 * f_year) - 0.002697 * cos(3 * f_year) + 0.00148 * sin(3 * f_year)


def hour_angle_sunrise_sunset(latitude, decl=sol_declination()):
    return acos_dg((cos_dg(SUNRISE_SUNSET_ZENITH) / (cos_dg(latitude) * cos_dg(decl))) -
                   tan_dg(latitude * tan(decl)))


def hour_angle_civil_twilight(latitude, decl=sol_declination()):
    return acos_dg((cos_dg(CIVIL_TWILIGHT_ZENITH) / (cos_dg(latitude) * cos_dg(decl))) -
                   tan_dg(latitude * tan(decl)))


def sunrise(longitude, latitude, timezone, ha=None, eqtime=eq_time()):
    if ha is None:
        ha = hour_angle_sunrise_sunset(latitude)
    return round(720 - 4 * (longitude + ha) - eqtime + 60 * timezone) * 60


def sunset(longitude, latitude, timezone, ha=None, eqtime=eq_time()):
    if ha is None:
        ha = hour_angle_sunrise_sunset(latitude)
    return round(720 - 4 * (longitude - ha) - eqtime + 60 * timezone) * 60


def civil_twilight(longitude, latitude, timezone, ha=None, eqtime=eq_time()):
    if ha is None:
        ha = hour_angle_civil_twilight(latitude)
    return round(720 - 4 * (longitude - ha) - eqtime + 60 * timezone) * 60


def sol_noon(longitude, timezone, eqtime=eq_time()):
    return round(720 - 4 * longitude - eqtime + 60 * timezone) * 60


def timetuple(latitude, longitude, timezone):
    return (
        sunrise(longitude, latitude, timezone), sol_noon(longitude, timezone),
        sunset(longitude, latitude, timezone), civil_twilight(longitude, latitude, timezone))


def __get_daytime_dt(daytime_func, latitude: float, longitude: float, date: datetime, timezone: float) -> datetime:
    fy = fractional_year(date)
    eqt = eq_time(fy)
    dec = sol_declination(fy)

    if daytime_func is civil_twilight:
        ha = hour_angle_civil_twilight(latitude, dec)
    else:
        ha = hour_angle_sunrise_sunset(latitude, dec)

    if daytime_func is sol_noon:
        daytime_seconds = daytime_func(longitude, timezone, eqt)
    else:
        daytime_seconds = daytime_func(longitude, latitude, timezone, ha, eqt)

    dt = datetime(date.year, date.month, date.day) + \
        timedelta(seconds=daytime_seconds)

    return dt


def get_sunset_datetime(latitude: float, longitude: float, date: datetime, timezone: float) -> datetime:
    return __get_daytime_dt(sunset, latitude, longitude, date, timezone)


def get_sunrise_datetime(latitude: float, longitude: float, date: datetime, timezone: float) -> datetime:
    return __get_daytime_dt(sunrise, latitude, longitude, date, timezone)


def get_noon_datetime(latitude: float, longitude: float, date: datetime, timezone: float) -> datetime:
    return __get_daytime_dt(sol_noon, latitude, longitude, date, timezone)


def get_civil_twilight_datetime(latitude: float, longitude: float, date: datetime, timezone: float) -> datetime:
    return __get_daytime_dt(civil_twilight, latitude, longitude, date, timezone)
