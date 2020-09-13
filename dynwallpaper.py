#!/bin/python3

from localization import ip_geolocation, get_external_ip
from solar_time import timetuple
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as DOM
import subprocess


__DEFAULT_GEOLOCATION__ = (0, 0)
__DAY_TIMES__ = ('sunrise', 'noon', 'day', 'sunset', 'night')
__DAY_LEN__ = 24 * 3600
__STATIC_NOON_DUR__ = 600  # default duration for noon in seconds


# --------------------- miscellaneous -------------------------


def flatten(l): return [item for sublist in l for item in sublist]


def get_host_timezone():
    output = subprocess.Popen(
        "date +'%z'", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
    output = output[0].decode('ascii')
    return int(output[:3]) + int(output[3:])


# ---------------- Dynamic Wallpaper class --------------------

class DynWallpaper:
    def __init__(self):
        self.__latitude, self.__longitude = __DEFAULT_GEOLOCATION__
        self.__timezone = get_host_timezone()
        self.__external_ip = None
        self.__theme = None
        self.__sunrise, self.__snoon, self.__sunset = timetuple(
            self.__latitude, self.__longitude, self.__timezone)

    def updateGeolocation(self):
        self.__external_ip = get_external_ip()
        if self.__external_ip != None:
            coords = ip_geolocation(self.__external_ip)
            if coords != None:
                self.__latitude, self.__longitude = coords
                return True
        self.__latitude, self.__longitude = __DEFAULT_GEOLOCATION__
        return False

    def updateSoltime(self):
        self.__sunrise, self.__snoon, self.__sunset = timetuple(
            self.__latitude, self.__longitude, self.__timezone)

    def loadTheme(self, theme_filepath):
        try:
            with open(theme_filepath, 'r') as f:
                self.__theme = json.load(f)
                # TODO create self.__theme validation function
                return True
        except IOError:
            print("Could not read file: ", theme_filepath)
        except json.JSONDecodeError:
            print("Error occured while trying to parse JSON file: ", theme_filepath)

        self.__theme = None
        return False

    def __calculate_timings(self, transition_time):
        timings = {'sunrise': [], 'noon': [],
                   'day': [], 'sunset': [], 'night': []}
        sunrise_dur = self.__snoon - self.__sunrise
        noon_dur = __STATIC_NOON_DUR__ + transition_time
        day_dur = (self.__sunset - self.__snoon) // 2
        sunset_dur = day_dur
        night_dur = __DAY_LEN__ - sunrise_dur - noon_dur - day_dur - sunset_dur

        durations = [sunrise_dur, noon_dur, day_dur, sunset_dur, night_dur]

        for i, daytime in enumerate(__DAY_TIMES__):
            # current daytime -> next daytime  : duration
            trans_dur = transition_time * \
                len(self.__theme["filelist"][daytime])
            sub_dur = durations[i] - trans_dur
            static_dur = [sub_dur // len(self.__theme["filelist"][daytime])
                          for x in range(len(self.__theme["filelist"][daytime]))]

            # fix static time
            if sum(static_dur) != sub_dur:
                static_dur.append(sub_dur - sum(static_dur) + static_dur.pop())

            timings[daytime] = [(x, transition_time) for x in static_dur]

        validation_sum = sum(flatten(flatten(timings.values())))
        if validation_sum != __DAY_LEN__:
            raise Exception(
                f"Total animation length not equal day length! It is: {validation_sum}, should be {__DAY_LEN__}")

        return timings

    def generateXML(self, xmlfilepath, transition_time=600):

        timings = self.__calculate_timings(transition_time)

        root = ET.Element("background")
        starttime = ET.SubElement(root, "starttime")

        ET.SubElement(starttime, "year").text = "2020"
        ET.SubElement(starttime, "month").text = "1"
        ET.SubElement(starttime, "day").text = "1"
        ET.SubElement(starttime, "hour").text = f"{int(self.__sunrise / 3600)}"
        ET.SubElement(
            starttime, "minute").text = f"{int((self.__sunrise % 3600) / 60)}"
        ET.SubElement(starttime, "second").text = "0"

        filename_template = str(self.__theme['wallpaper_filename'])

        for count, daytime in enumerate(__DAY_TIMES__):
            for wallpaper_index in range(len(self.__theme["filelist"][daytime])):

                wallpaper = filename_template.replace(
                    '*', str(self.__theme["filelist"][daytime][wallpaper_index]))

                # static background
                tmp = ET.SubElement(root, "static")

                ET.SubElement(tmp, "file").text = wallpaper
                ET.SubElement(tmp, "duration").text = str(
                    timings[daytime][wallpaper_index][0])

                # transition to next background
                tmp = ET.SubElement(root, "transition", type="overlay")
                ET.SubElement(tmp, "duration").text = str(
                    timings[daytime][wallpaper_index][1])
                ET.SubElement(tmp, "from").text = wallpaper

                if wallpaper_index + 1 >= len(self.__theme["filelist"][daytime]):
                    next_wallpaper = filename_template.replace(
                        '*', str(self.__theme["filelist"][__DAY_TIMES__[(count + 1) % len(__DAY_TIMES__)]][0]))
                else:
                    next_wallpaper = filename_template.replace(
                        '*', str(self.__theme["filelist"][daytime][wallpaper_index + 1]))

                ET.SubElement(tmp, "to").text = next_wallpaper

        xmlheader = DOM.Document().toxml()
        xmlstr = DOM.parseString(ET.tostring(root)).toprettyxml(
            indent="   ")[len(xmlheader) + 1:]

        with open(xmlfilepath, 'w') as f:
            f.write('<!-- Generated by --> \n')
            f.write(xmlstr)

    def getDataSummary(self):
        return {'lat': self.__latitude, 'lon': self.__longitude, 'timezone': self.__timezone,
                'extip': self.__external_ip, 'self.__theme': self.__theme, 'sunrise': self.__sunrise,
                'snoon': self.__snoon, 'sunset': self.__sunset}


if __name__ == "__main__":
    dw = DynWallpaper()
    dw.updateGeolocation()
    dw.updateSoltime()
    dw.loadTheme('./theme.json')
    print(dw.getDataSummary())
    dw.generateXML('./test.xml')
