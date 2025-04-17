import json
import requests
from urllib.parse import quote

from tools.utils import RoutineResponse
from datetime import datetime, timedelta, timezone


date_format = "%Y-%m-%d"


def view_weather(region_name: str, date_from: str = None, date_to: str = None):
    if not date_from:
        date_from = (datetime.now(timezone.utc) +
                     timedelta(hours=7)).strftime(date_format)
    try:
        if date_to:
            date_to = (datetime.strptime(date_to, date_format) +
                       timedelta(hours=7)).strftime(date_format)
        else:
            date_to = date_from
    except:
        return f"[ERROR]: Mabe have a error while checking the date_from and date_to"

    res = requests.get(
        f'https://nominatim.openstreetmap.org/search?q={quote(region_name)}&format=json', headers={
            'User-Agent': 'Mozilla/5.0 (compatible; MyWeatherApp/1.0)'
        })

    if res.status_code not in [200, 201] or not res.json():
        return f"[ERROR] No long, lat data for region with name {region_name}"

    location = res.json()
    long, lat = location[0].get("lon", 0), location[0].get("lat", 0)

    res = requests.get(
        f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&start_date={date_from}&end_date={date_to}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,windspeed_10m_max,uv_index_max,sunrise,sunset&timezone=Asia%2FBangkok')
    if res.status_code not in [200, 201] or not res.json():
        return f"[ERROR] No data for weather of region with name {region_name}"

    return RoutineResponse("The data weather of %s is: %s" % (region_name, json.dumps(res.json())))
