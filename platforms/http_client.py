import requests
from models import PlatformError

TIMEOUT_SECONDS = 10


def get_json(platform_name, url, headers=None, params=None):
    try:
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as error:
        raise PlatformError(f"{platform_name}: could not connect ({type(error).__name__})") from error

    if response.status_code != 200:
        raise PlatformError(f"{platform_name}: request failed with status {response.status_code}")

    try:
        return response.json()
    except ValueError as error:
        raise PlatformError(f"{platform_name}: response was not valid JSON") from error