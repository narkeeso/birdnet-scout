"""Analyze audio recordings using BirdNET and store predictions in a database."""

import fnmatch
import sqlite3
import os
from datetime import datetime
from pathlib import Path

from birdnet import SpeciesPredictions, predict_species_within_audio_file  # type: ignore
from birdnet.location_based_prediction import predict_species_at_location_and_time  # type: ignore
from loguru import logger

recordings_dir = Path("recordings")
recordings_dir.mkdir(exist_ok=True)

PREDICTION_BLACKLIST = ["Dog", "Human ", "Engine", "Gun"]


def is_invalid_prediction(prediction: str) -> bool:
    """
    Check if the prediction is invalid (in the blacklist).
    """
    return any(prediction.startswith(blacklist) for blacklist in PREDICTION_BLACKLIST)


def get_location_species():
    # get calendar week
    week = datetime.now().isocalendar()[1]

    # Defaults to Columbia, one of the most biodiverse bird regions in the world
    lat, long = os.environ.get("BIRDNET_SCOUT_COORDINATES", "4.5709,74.2973").split(",")

    results = predict_species_at_location_and_time(
        float(lat), float(long), week=week
    ).items()

    species = {}

    for prediction, confidence in results:
        species[prediction] = float(confidence)

    logger.debug(
        f"Found {len(species)} species at location ({lat}, {long}) for week {week}."
    )

    return species


def analyze(db: sqlite3.Connection):
    """
    Analyze audio recordings in the recordings directory and store predictions in the database.
    """

    wav_files = [f for f in os.listdir(recordings_dir) if fnmatch.fnmatch(f, "*.wav")]

    logger.debug(f"Found {len(wav_files)} recordings to analyze.")

    cursor = db.cursor()

    location_species = get_location_species()

    for filename in wav_files:
        logger.debug(f"Analyzing recording {filename}")
        audio_path = recordings_dir / filename
        predictions = SpeciesPredictions(
            predict_species_within_audio_file(audio_path, min_confidence=0.5)
        )

        count = 0
        for interval, result in predictions.items():
            for prediction, audio_confidence in result.items():
                scientific_name, common_name = prediction.split("_")

                if is_invalid_prediction(scientific_name):
                    logger.debug(f"Skipping blacklisted prediction: {prediction}")
                    continue

                loc_confidence = location_species.get(prediction, 0)

                cursor.execute(
                    """
                    INSERT INTO predictions (recording_key, interval, scientific_name, common_name, audio_confidence, location_confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        filename,
                        f"{interval[0]},{interval[1]}",
                        scientific_name,
                        common_name,
                        float(audio_confidence),
                        loc_confidence,
                        datetime.now().isoformat(),
                    ),
                )
                count += 1

        db.commit()
        logger.info(f"Inserted {count} predictions for {filename} into the database.")

        os.remove(audio_path)
        logger.debug(f"Removed recording {filename} after analysis.")
