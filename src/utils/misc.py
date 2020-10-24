#!/bin/python3

from datetime import datetime
from collections.abc import Collection

# --------------------- miscellaneous -------------------------


def flatten(lst: Collection) -> list:
    return [item for sublist in lst for item in sublist]


# ----------------------- timezone ----------------------------

def local_tzoffset() -> float:
    deltatime = (datetime.now() - datetime.utcnow()).total_seconds()
    tz = round(deltatime) / 3600
    return tz
