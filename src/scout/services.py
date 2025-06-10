import json
from datetime import datetime

import arrow
import requests
from loguru import logger

from . import database

# The number of detections required to be connsidered valid
SAMPLE_THRESHOLD = 3


def init():
    table = database.db["config"]
    config = table.find_one(id=1)  # type: ignore
    if not config:
        logger.info("Creating config table")
        table.insert({"id": 1, "location": "{}"})  # type: ignore


def get_config():
    table = database.db["config"]
    config = table.find_one(id=1)  # type: ignore
    return {"location": json.loads(config["location"])}


def get_latest_detections():
    result = database.db.query(
        f"""
        SELECT
            COUNT(scientific_name) AS sample_count,
            common_name,
            scientific_name,
            AVG(audio_confidence) AS audio_confidence,
            MAX(location_confidence) AS location_confidence,
            location AS location,
            MAX(recording_start) AS created_at
        FROM detections
        GROUP BY scientific_name, common_name, location, DATE(datetime(recording_start, 'localtime'))
        HAVING COUNT(scientific_name) >= {SAMPLE_THRESHOLD}
        ORDER BY created_at DESC
        """
    )

    results = {}

    for row in result:
        if not row:
            return

        created_at = arrow.get(row.get("created_at", ""))
        date = created_at.to("local").format("YYYY-MM-DD")

        if results.get(date) is None:
            results[date] = []

        results[date].append(row)

    return results


def update_location():
    response = requests.get("https://api.ipify.org", timeout=5)
    ip_address = response.text
    response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
    data = response.json()
    table = database.db["config"]
    table.update({"id": 1, "location": json.dumps(data)}, ["id"])  # type: ignore
    return data


def get_total_discovered() -> int:
    result = database.db.query(
        f"""
        SELECT DISTINCT scientific_name
        FROM detections
        GROUP BY scientific_name 
        HAVING COUNT(scientific_name) > {SAMPLE_THRESHOLD};
        """
    )

    count = 0
    for _ in result:
        count += 1
    return count
