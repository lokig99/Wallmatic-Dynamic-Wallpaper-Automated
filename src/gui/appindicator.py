#!/bin/python3
import os
import signal
from gi import require_versions

from definitions.dirs import ICONS_DIR

require_versions({'Gtk': '3.0', 'AppIndicator3': '0.1', 'Notify': '0.7'})
from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify


APPINDICATOR_ID = 'wallmatic'
TASKBAR_ICON_PATH = os.path.join(ICONS_DIR, 'wallmatic-icon-nobackground.svg')
TASKBAR_ICON_PATH_DARK = os.path.join(
    ICONS_DIR, 'wallmatic-icon-nobackground-dark.svg')

LABEL_ENABLE_NIGHT_MODE = "Enable Night Mode"
LABEL_DISABLE_NIGHT_MODE = "Disable Night Mode"
LABEL_QUIT = "Quit"

################################### global variables ####################################

__AppIndicator = appindicator.Indicator.new(
    APPINDICATOR_ID, TASKBAR_ICON_PATH, appindicator.IndicatorCategory.SYSTEM_SERVICES)

__night_mode_status = False


def get_night_mode_status() -> bool:
    global __night_mode_status
    return __night_mode_status

#########################################################################################



def main():
    global __AppIndicator
    __AppIndicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    __AppIndicator.set_menu(build_menu())
    notify.init(APPINDICATOR_ID)
    gtk.main()


def build_menu():
    menu = gtk.Menu()
    item_quit = gtk.MenuItem(label=LABEL_QUIT)
    item_quit.connect('activate', quit)
    item_night_mode = gtk.MenuItem(label=LABEL_ENABLE_NIGHT_MODE)
    item_night_mode.connect('activate', night_mode)
    menu.append(item_night_mode)
    menu.append(item_quit)
    menu.show_all()
    return menu


def quit(_):
    notify.uninit()
    gtk.main_quit()


def night_mode(item: gtk.MenuItem):
    global __night_mode_status
    global __AppIndicator

    if __night_mode_status:
        __night_mode_status = False
        __AppIndicator.set_icon(TASKBAR_ICON_PATH)
        item.set_label(LABEL_ENABLE_NIGHT_MODE)
    else:
        __night_mode_status = True
        __AppIndicator.set_icon(TASKBAR_ICON_PATH_DARK)
        item.set_label(LABEL_DISABLE_NIGHT_MODE)
