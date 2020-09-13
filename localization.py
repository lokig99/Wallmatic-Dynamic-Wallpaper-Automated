#!/bin/python3

from json import loads
import requests

RETRY_LIMIT = 5


def send_request(api_addr):
    """
    Arg: API http address\n
    Returns: requested data in form of string\n
    If request fails function returns None
    """
    attempts = 1
    while attempts <= RETRY_LIMIT:
        try:
            r = requests.get(api_addr)
            r.raise_for_status()
            return r.text
        except requests.exceptions.HTTPError as errhttp:
            print('HTTP Error: ', errhttp)
        except requests.exceptions.ConnectionError as errc:
            print('Connection Error: ', errc)
        except requests.exceptions.Timeout as errt:
            print('Connection timeout: ', errt)

        print(
            f'Trying to send request again. Attempt no. {attempts} of {RETRY_LIMIT}')
        attempts += 1

    return None


def get_external_ip():
    return send_request('https://api.ipify.org')


def ip_geolocation(ip):
    location = loads(send_request(f'https://api.ipgeolocationapi.com/geolocate/{ip}'))
    if location == None:
        return None
    return location['geo']['latitude'], location['geo']['longitude']

