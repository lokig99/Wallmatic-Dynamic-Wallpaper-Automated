#!/bin/python3

import time
import gi

gi.require_version('Geoclue', '2.0')
from gi.repository import Geoclue
from multiprocessing.pool import ThreadPool

TIMEOUT = 3  # geolocation request timeout in seconds
INTERVAL = 0.01


def __get_location(_):
    clue = Geoclue.Simple.new_sync(
        'localization', Geoclue.AccuracyLevel.NEIGHBORHOOD, None)
    location = clue.get_location()
    return location.get_property('latitude'), location.get_property('longitude')


def get_geolocation():
    pool = ThreadPool(processes=1)
    locator = pool.apply_async(__get_location, range(1))

    timer = 0
    result = None

    while timer < TIMEOUT:
        timer += INTERVAL

        if locator.ready():
            result = locator.get()
            break

        time.sleep(INTERVAL)

    pool.close()
    return result
