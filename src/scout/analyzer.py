"""Analyze audio recordings using BirdNET and store predictions in a database."""

import fnmatch
import os
from datetime import datetime
from pathlib import Path

from birdnet import SpeciesPredictions, predict_species_within_audio_file  # type: ignore
from birdnet.location_based_prediction import predict_species_at_location_and_time  # type: ignore
from loguru import logger

from .database import db

recordings_dir = Path("recordings")
recordings_dir.mkdir(exist_ok=True)

coordinates = os.environ.get("BIRDNET_SCOUT_COORDINATES")

PREDICTION_BLACKLIST = ["Dog", "Human ", "Engine", "Gun"]


def is_invalid_prediction(prediction: str) -> bool:
    """
    Check if the prediction is invalid (in the blacklist).
    """
    return any(prediction.startswith(blacklist) for blacklist in PREDICTION_BLACKLIST)


def get_location_species():
    if not coordinates:
        logger.warning(
            "No coordinates provided. Skipping location-based species prediction."
        )
        return {}

    # get calendar week
    week = datetime.now().isocalendar()[1]

    # Defaults to Columbia, one of the most biodiverse bird regions in the world

    lat, long = coordinates.split(",")

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


def analyze():
    """
    Analyze audio recordings in the recordings directory and store predictions in the database.
    """

    wav_files = [f for f in os.listdir(recordings_dir) if fnmatch.fnmatch(f, "*.wav")]

    logger.debug(f"Found {len(wav_files)} recordings to analyze.")

    location_species = get_location_species()

    for filename in wav_files:
        recording_start, recording_end = filename.split(".")[0].split("_")
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

                table = db["detections"]

                table.insert(  # type: ignore
                    {
                        "recording_start": datetime.fromtimestamp(int(recording_start)),
                        "recording_end": datetime.fromtimestamp(int(recording_end)),
                        "interval": f"{interval[0]},{interval[1]}",
                        "scientific_name": scientific_name,
                        "common_name": common_name,
                        "audio_confidence": float(audio_confidence),
                        "location": coordinates,
                        "location_confidence": loc_confidence,
                        "created_at": datetime.now(),
                    }
                )

                count += 1

        logger.info(f"Inserted {count} predictions for {filename} into the database.")

        os.remove(audio_path)
        logger.debug(f"Removed recording {filename} after analysis.")
