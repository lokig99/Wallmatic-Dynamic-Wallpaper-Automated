#!/bin/python3

from datetime import datetime
import localization
import solartime
import json
import xml.etree.ElementTree as Et
import xml.dom.minidom as dom
import subprocess
import os

VERSION = 'alpha 1.0'

MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
THEMES_DIR = f'{MAIN_DIR}/themes'
WALLPAPER_XML_DIR = f'{MAIN_DIR}/wallpaper-xml'

DEFAULT_GEOLOCATION = (0, 0)
DAY_TIMES = ('sunrise', 'noon', 'day', 'sunset', 'night')
DAY_LENGTH = 24 * 3600  # 24 hours (in seconds)

# total noon duration (in seconds) including transition to daytime wallpaper
NOON_DURATION = 1800

# how long it takes to get actually dark after sunset (in seconds)
# rough average approximation based on nautical twilight for latitudes between 0 to 70 degrees (N/S)
TWILIGHT_DURATION = 3600


# --------------------- miscellaneous -------------------------

def flatten(lst): return [item for sublist in lst for item in sublist]


def get_host_timezone():
    output = subprocess.Popen(
        "date +'%z'", stdout=subprocess.PIPE, shell=True).communicate()
    tz = output[0].decode('ascii')
    tz_sign = int(f'{tz[0]}1')
    return tz_sign * float(f'{tz[1:3]}.{tz[3:]}')


# ---------------- Dynamic Wallpaper class --------------------

class DynWallpaper:
    def __init__(self):
        self.__latitude, self.__longitude = DEFAULT_GEOLOCATION
        self.__timezone = get_host_timezone()
        self.__theme_dir = None
        self.__sunrise, self.__snoon, self.__sunset = solartime.timetuple(
            self.__latitude, self.__longitude, self.__timezone)

    def set_geolocation_online(self):
        res = localization.get_geolocation()
        if res is not None:
            self.__latitude, self.__longitude = res
            return True

        self.__latitude, self.__longitude = DEFAULT_GEOLOCATION
        return False

    def set_geolocation_manually(self, latitude, longitude):
        self.__latitude, self.__longitude = latitude, longitude

    def update_soltime(self):
        self.__sunrise, self.__snoon, self.__sunset = solartime.timetuple(
            self.__latitude, self.__longitude, self.__timezone)

    def set_theme_directory(self, theme_filepath):
        self.__theme_dir = os.path.abspath(theme_filepath)

    def set_timezone_host(self):
        self.__timezone = get_host_timezone()

    def set_timezone(self, timezone):
        self.__timezone = timezone

    def __load_theme(self):
        try:
            with open(f'{self.__theme_dir}/theme.json', 'r') as f:
                theme = json.load(f)
                # TODO create self.__theme_dir validation function
                return theme
        except IOError:
            print("Could not read file: ", self.__theme_dir)
        except json.JSONDecodeError:
            print("Error occurred while trying to parse JSON file: ",
                  self.__theme_dir)

        self.__theme_dir = None
        return None

    def __calculate_timings(self, theme, transition_time):
        timings = {'sunrise': [], 'noon': [],
                   'day': [], 'sunset': [], 'night': []}
        sunrise_dur = self.__snoon - self.__sunrise
        day_dur = (self.__sunset - self.__snoon - NOON_DURATION) * (2 / 3)
        sunset_dur = (self.__sunset - self.__snoon -
                      NOON_DURATION) - day_dur + TWILIGHT_DURATION
        night_dur = DAY_LENGTH - sunrise_dur - NOON_DURATION - day_dur - sunset_dur

        durations = [sunrise_dur, NOON_DURATION,
                     day_dur, sunset_dur, night_dur]

        for i, daytime in enumerate(DAY_TIMES):
            # current daytime -> next daytime  : duration
            trans_time = transition_time
            if trans_time * len(theme["filelist"][daytime]) >= durations[i]:
                print(
                    f'WARNING: Transitions take longer than duration of {daytime}! Fixing timings...')
                trans_time = (
                    durations[i] - len(theme["filelist"][daytime])) // len(theme["filelist"][daytime])

            sub_dur = durations[i] - trans_time * \
                len(theme["filelist"][daytime])
            static_dur = [sub_dur // len(theme["filelist"][daytime])
                          for _ in range(len(theme["filelist"][daytime]))]

            # fix static time
            if sum(static_dur) != sub_dur:
                static_dur.append(sub_dur - sum(static_dur) + static_dur.pop())

            timings[daytime] = [(x, trans_time) for x in static_dur]

        validation_sum = sum(flatten(flatten(timings.values())))
        if validation_sum != DAY_LENGTH:
            raise Exception(
                f"Total animation length does not equal 24 hours! It is: {validation_sum}, should be {DAY_LENGTH}")

        return timings

    def generate_xml(self, target_directory_path, transition_time=600):
        theme = self.__load_theme()
        timings = self.__calculate_timings(theme, transition_time)

        root = Et.Element("background")
        start_time = Et.SubElement(root, "starttime")

        Et.SubElement(start_time, "year").text = "2020"
        Et.SubElement(start_time, "month").text = "1"
        Et.SubElement(start_time, "day").text = "1"
        Et.SubElement(start_time, "hour").text = f"{self.__sunrise // 3600}"
        Et.SubElement(
            start_time, "minute").text = f"{(self.__sunrise % 3600) // 60}"
        Et.SubElement(start_time, "second").text = "0"

        filename_template = f'{self.__theme_dir}/{theme["wallpaper_filename"]}'

        for count, daytime in enumerate(DAY_TIMES):
            for wallpaper_index in range(len(theme["filelist"][daytime])):
                wallpaper = filename_template.replace(
                    '*', str(theme["filelist"][daytime][wallpaper_index]))

                # static background
                tmp = Et.SubElement(root, "static")

                Et.SubElement(tmp, "file").text = wallpaper
                Et.SubElement(tmp, "duration").text = str(
                    timings[daytime][wallpaper_index][0])

                # transition to next background
                tmp = Et.SubElement(root, "transition", type="overlay")
                Et.SubElement(tmp, "duration").text = str(
                    timings[daytime][wallpaper_index][1])
                Et.SubElement(tmp, "from").text = wallpaper

                if wallpaper_index + 1 >= len(theme["filelist"][daytime]):
                    next_wallpaper = filename_template.replace(
                        '*', str(theme["filelist"][DAY_TIMES[(count + 1) % len(DAY_TIMES)]][0]))
                else:
                    next_wallpaper = filename_template.replace(
                        '*', str(theme["filelist"][daytime][wallpaper_index + 1]))

                Et.SubElement(tmp, "to").text = next_wallpaper

        xml_header = dom.Document().toxml()
        xml_str = dom.parseString(Et.tostring(root)).toprettyxml(
            indent="   ")[len(xml_header) + 1:]

        xml_path = f'{target_directory_path}/{theme["credits"]}_{theme["theme_title"].replace(" ", "_")}'
        xml_path = f'{xml_path}-{datetime.now().strftime("%d%m%Y")}.xml'

        with open(xml_path, 'w') as f:
            f.write(
                f'<!-- Generated by Wallmatic {VERSION} by M-LoKi-G --> \n')
            f.write(xml_str)
        return xml_path

    def get_data_summary(self):
        return {'lat': self.__latitude, 'lon': self.__longitude, 'timezone': self.__timezone, 'sunrise': self.__sunrise,
                'snoon': self.__snoon, 'sunset': self.__sunset, 'theme': self.__theme_dir}


# ------------------ User Interface ----------------------------


def list_valid_themes():
    themes_list = []
    for d in os.listdir(THEMES_DIR):
        d_abspath = f'{THEMES_DIR}/{d}'
        if os.path.isdir(d_abspath) and 'theme.json' in os.listdir(d_abspath):
            themes_list.append(d)
    return themes_list


def select_theme():
    themes = sorted(list_valid_themes())
    if len(themes) == 0:
        raise Exception(f'No themes available in {THEMES_DIR}')

    print('Available wallpaper themes:\n')
    for i, theme in enumerate(themes):
        print(f'[{i}]\t{theme.replace("_", " ")}')
    choice = input('\nselect theme (eg: 1, default=0): ')
    if not choice.isdigit() or int(choice) >= len(themes):
        choice = 0
    return f'{THEMES_DIR}/{themes[int(choice)]}'


# --------------------------------------------------------------

if __name__ == "__main__":
    print(f"Wallmatic by M-LoKi-G (version: {VERSION})\n")

    dw = DynWallpaper()

    print('Finding your current location...\n')
    dw.set_geolocation_online()

    dw.update_soltime()

    dw.set_theme_directory(select_theme())

    # debug info
    print('\n DEBUG INFO\n')
    print(json.dumps(dw.get_data_summary(), indent=4))

    if not os.path.exists(WALLPAPER_XML_DIR):
        os.mkdir(WALLPAPER_XML_DIR)

    xmlpath = os.path.abspath(dw.generate_xml(WALLPAPER_XML_DIR, 1800))

    # reset wallpaper
    # subprocess.call(
    #     f'gsettings reset org.gnome.desktop.background picture-uri', shell=True)

    # set newly generated wallpaper
    subprocess.call(
        f'gsettings set org.gnome.desktop.background picture-uri "file:///{xmlpath}"', shell=True)


    subprocess.call(
        f'gsettings set org.gnome.shell.extensions.user-theme name Pop-dark', shell=True)

    subprocess.call(
        f'gsettings set org.gnome.desktop.interface gtk-theme Pop-dark', shell=True)
