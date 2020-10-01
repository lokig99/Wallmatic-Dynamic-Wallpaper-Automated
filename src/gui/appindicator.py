#!/bin/python3

import os
import signal
from gi import require_versions

require_versions({'Gtk': '3.0', 'AppIndicator3': '0.1', 'Notify': '0.7'})
from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify

from definitions.dirs import ICONS_DIR


APPINDICATOR_ID = 'wallmatic'
TASKBAR_ICON_PATH = os.path.join(ICONS_DIR, 'wallmatic-icon-nobackground.svg')


def main():
    indicator = appindicator.Indicator.new(
        APPINDICATOR_ID, TASKBAR_ICON_PATH, appindicator.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(build_menu())
    notify.init(APPINDICATOR_ID)
    gtk.main()


def build_menu():
    menu = gtk.Menu()
    item_quit = gtk.MenuItem(label='Quit')
    item_quit.connect('activate', quit)
    menu.append(item_quit)
    menu.show_all()
    return menu


def quit(_):
    notify.uninit()
    gtk.main_quit()