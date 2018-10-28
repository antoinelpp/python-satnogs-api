from __future__ import print_function
import re

import requests


NETWORK_DEV_BASE_URL = 'https://network-dev.satnogs.org'
NETWORK_BASE_URL = 'https://network.satnogs.org'
DB_BASE_URL = 'https://db.satnogs.org'
DB_DEV_BASE_URL = 'https://db-dev.satnogs.org'


def get_paginated_endpoint(url, max_entries=None):
    r = requests.get(url=url)
    r.raise_for_status()

    data = r.json()

    while 'next' in r.links and (not max_entries or len(data) < max_entries):
        next_page_url = r.links['next']['url']

        r = requests.get(url=next_page_url)
        r.raise_for_status()

        data.extend(r.json())

    return data


def fetch_observation_data_from_id(norad_id, start, end, prod=True):
    # Get all observations of the satellite
    # with the given `norad_id` in the given timeframe
    # https://network.satnogs.org/api/observations/?satellite__norad_cat_id=25544&start=2018-06-10T00:00&end=2018-06-15T00:00

    query_str = '{}/api/observations/' \
                '?satellite__norad_cat_id={}&start={}&end={}'

    url = query_str.format(NETWORK_BASE_URL if prod else NETWORK_DEV_BASE_URL,
                           norad_id,
                           start.isoformat(),
                           end.isoformat())

    observations = get_paginated_endpoint(url)

    # Current prod is broken and can't filter on NORAD ID correctly,
    # use client-side filtering instead
    observations = list(observation for observation in observations
                        if observation['norad_cat_id'] == norad_id)

    return observations


def fetch_observation_data(observation_ids, prod=True):
    # Get station location from the observation via the observation_id

    observations = []
    for observation_id in observation_ids:
        base_url = (NETWORK_BASE_URL if prod else NETWORK_DEV_BASE_URL)
        r = requests.get(url='{}/api/observations/{}/'.format(base_url,
                                                              observation_id))
        r.raise_for_status()
        observations.append(r.json())

    return observations


def fetch_ground_station_data(ground_station_ids, prod=True):
    # Fetch ground station metadata from network
    ground_stations = []
    for ground_station_id in ground_station_ids:
        # Skip frames from deleted groundstations, indidcated as ID 'None'
        if str(ground_station_id) == 'None':
            print("Skipping groundstation 'None'.")
            continue

        base_url = (NETWORK_BASE_URL if prod else NETWORK_DEV_BASE_URL)
        r = requests.get(url='{}/api/stations/{}/'.format(base_url,
                                                          ground_station_id))
        r.raise_for_status()

        ground_stations.append(r.json())
    return ground_stations


def fetch_satellite_data(norad_cat_id):
    # Fetch satellite metadata from network
    r = requests.get(url='{}/api/satellites/{}/'.format(DB_BASE_URL,
                                                        norad_cat_id))
    r.raise_for_status()

    return r.json()


def fetch_tle_of_observation(observation_id, prod=True):
    base_url = (NETWORK_BASE_URL if prod else NETWORK_DEV_BASE_URL)
    url = '{}/observations/{}/'.format(base_url,
                                       observation_id)
    r = requests.get(url=url)
    observation_page_html = r.text

    regex = r"<pre>1 (.*)<br>2 (.*)</pre>"
    matches = re.search(regex, observation_page_html)

    obs_tle_2 = '1 ' + matches.group(1)
    obs_tle_3 = '2 ' + matches.group(2)

    return [obs_tle_2, obs_tle_3]


def fetch_telemetry(norad_id, url):
    # http://db-dev.satnogs.org/api/telemetry/?satellite=43595

    query_str = '{}/api/telemetry/?satellite={}'

    url = query_str.format(url, norad_id)

    telemetry = get_paginated_endpoint(url)

    return telemetry


def fetch_transmitters(norad_id, url):
    # http://db-dev.satnogs.org/api/transmitters/?satellite__norad_cat_id=25544

    query_str = '{}/api/transmitters/?satellite__norad_cat_id={}'

    url = query_str.format(url, norad_id)

    transmitters = get_paginated_endpoint(url)
    return transmitters


def fetch_satellites(max_entries, url):
    query_str = '{}/api/satellites/'
    url = query_str.format(url)

    satellites = get_paginated_endpoint(url, max_entries=max_entries)
    return satellites


def post_telemetry(norad_id,
                   source,  # Receiver Callsign
                   lon,
                   lat,
                   timestamp,
                   frame,
                   base_url=DB_DEV_BASE_URL):
    payload = {'noradID': norad_id,
               'source': source,
               'timestamp': timestamp,
               'latitude': lat,
               'longitude': lon,
               'frame': frame}

    url = '{}/api/telemetry/'.format(base_url)
    r = requests.post(url, data=payload)

    if r.status_code != 201:
        print('ERROR {}: {}'.format(r.status_code, r.text))
