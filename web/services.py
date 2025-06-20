import arrow
import requests

from . import models


def update_location(config: models.Config) -> models.Config:
    session = requests.Session()

    response = session.get("https://api.ipify.org", timeout=5)
    ip_address = response.text

    if ip_address != config.location.get("query", ""):
        response = session.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
        data = response.json()
        config.location = data
        config.save()

    return config
