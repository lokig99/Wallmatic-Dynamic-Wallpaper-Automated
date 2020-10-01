#!/bin/python3

import gi
import time
from datetime import datetime
from multiprocessing.pool import ThreadPool

gi.require_version('Geoclue', '2.0')
from gi.repository import Geoclue

TIMEOUT = 5  # geolocation request timeout in seconds
INTERVAL = 0.01


def get_geolocation():
    def __get_location(_) -> tuple:
        clue = Geoclue.Simple.new_sync(
            'localization', Geoclue.AccuracyLevel.NEIGHBORHOOD, None)
        location = clue.get_location()
        return location.get_property('latitude'), location.get_property('longitude')

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
