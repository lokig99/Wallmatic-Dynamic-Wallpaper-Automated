#!/bin/python3

from datetime import datetime
from math import pi, cos, sin, acos, radians, tan

"""
General sun position calculations based on NOAA Global Monitoring Division data
for more information see: https://www.esrl.noaa.gov/gmd/grad/solcalc/solareqns.PDF
"""


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


def hour_angle_sunrise(latitude, decl=sol_declination()):
    return acos_dg((cos_dg(90.833) / (cos_dg(latitude) * cos_dg(decl))) -
                   tan_dg(latitude * tan(decl)))


def sunrise(longitude, latitude, timezone, ha=None, eqtime=eq_time()):
    if ha is None:
        ha = hour_angle_sunrise(latitude)
    return round(720 - 4 * (longitude + ha) - eqtime + 60 * timezone) * 60


def sunset(longitude, latitude, timezone, ha=None, eqtime=eq_time()):
    if ha is None:
        ha = hour_angle_sunrise(latitude)
    return round(720 - 4 * (longitude - ha) - eqtime + 60 * timezone) * 60


def sol_noon(longitude, timezone, eqtime=eq_time()):
    return round(720 - 4 * longitude - eqtime + 60 * timezone) * 60


def timetuple(latitude, longitude, timezone):
    return (
        sunrise(longitude, latitude, timezone), sol_noon(longitude, timezone), sunset(longitude, latitude, timezone))
