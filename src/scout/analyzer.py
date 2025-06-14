"""Analyze audio recordings using BirdNET and store predictions in a database."""

import fnmatch
import os
from datetime import datetime, timezone
from pathlib import Path

from birdnet import SpeciesPredictions, predict_species_within_audio_file  # type: ignore
from birdnet.location_based_prediction import predict_species_at_location_and_time  # type: ignore
from birdnet.models.v2m4.model_v2m4_tflite import AudioModelV2M4TFLite
from loguru import logger

from .database import db
from . import services

recordings_dir = Path("recordings")
recordings_dir.mkdir(exist_ok=True)

PREDICTION_BLACKLIST = ["Dog", "Human ", "Engine", "Gun", "Siren", "Power tools"]
DEFAULT_MODEL = AudioModelV2M4TFLite()


def is_invalid_prediction(prediction: str) -> bool:
    """
    Check if the prediction is invalid (in the blacklist).
    """
    return any(prediction.startswith(blacklist) for blacklist in PREDICTION_BLACKLIST)


def get_location_species(lat: str, long: str) -> dict:
    # get calendar week
    week = datetime.now().isocalendar()[1]
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

    location_species = {}
    coordinates = None

    config = services.get_config()
    location = config["location"]
    lat = location.get("lat", None)
    long = location.get("lon", None)

    if lat and long:
        location_species = get_location_species(lat, long)
        coordinates = f"{lat},{long}"
    else:
        logger.warning("No location set, skipping location prediction")

    for filename in wav_files:
        recording_start, duration = filename.split(".")[0].split("_")
        logger.debug(f"Analyzing recording {filename}")
        audio_path = recordings_dir / filename
        predictions = SpeciesPredictions(
            predict_species_within_audio_file(
                audio_path, min_confidence=0.6, custom_model=DEFAULT_MODEL
            )
        )

        logger.info(predictions)

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
                        "recording_start": datetime.fromtimestamp(
                            int(recording_start), tz=timezone.utc
                        ),
                        "recording_end": datetime.fromtimestamp(
                            int(recording_start) + int(duration), tz=timezone.utc
                        ),
                        "interval": f"{interval[0]},{interval[1]}",
                        "scientific_name": scientific_name,
                        "common_name": common_name,
                        "audio_confidence": float(audio_confidence),
                        "location": coordinates,
                        "location_confidence": loc_confidence,
                        "created_at": datetime.now(tz=timezone.utc),
                    }
                )

                count += 1

        logger.info(f"Inserted {count} predictions for {filename} into the database.")
        os.remove(audio_path)
        logger.debug(f"Removed recording {filename} after analysis.")


if __name__ == "__main__":
    analyze()
