#!/bin/python3

import os
import json
import subprocess
import threading

import daemon
import gui.appindicator as appindicator
from utils.theme import select_theme
from dynwallpaper import DynWallpaper
from definitions.version import VERSION, NAME, AUTHOR

def dynwallpaper_set_theme():
    print(f"{NAME} by {AUTHOR} (version: {VERSION})\n")

    Dynwall = DynWallpaper()

    print('Finding your current location...\n')
    Dynwall.set_geolocation_online()

    Dynwall.update_soltime()

    Dynwall.set_theme(select_theme())

    # debug info
    print('\n DEBUG INFO\n')
    print(json.dumps(Dynwall.get_data_summary(), indent=4))

    xmlpath = os.path.abspath(Dynwall.generate_xml())

    # set newly generated wallpaper
    subprocess.call(
        f'gsettings set org.gnome.desktop.background picture-uri "file:///{xmlpath}"', shell=True)


if __name__ == "__main__":
    theme_daemon = threading.Thread(target=daemon.loop, daemon=True)

    dynwallpaper_set_theme()

    print('\nstarting wallmatic daemon...')

    theme_daemon.start()

    print('\nApp is now running in background...\n')

    appindicator.main()
