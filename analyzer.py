"""Analyze audio recordings using BirdNET and store predictions in a database."""

import fnmatch
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

# Silences annoying tensorflow logs
import silence_tensorflow.auto  # type: ignore # noqa: F401 # pylint: disable=unused-import
from birdnet import SpeciesPredictions, predict_species_within_audio_file  # type: ignore
from birdnet.location_based_prediction import predict_species_at_location_and_time  # type: ignore
from birdnet.models.v2m4.model_v2m4_tflite import AudioModelV2M4TFLite
from loguru import logger


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
    session = requests.Session()

    # Get config settings
    response = session.get("http://localhost:5000/api/config", timeout=5)
    response.raise_for_status()
    csrftoken = session.cookies.get("csrftoken")
    config = response.json()

    wav_files = [f for f in os.listdir(recordings_dir) if fnmatch.fnmatch(f, "*.wav")]
    logger.debug(f"Found {len(wav_files)} recordings to analyze.")

    location_species = {}
    coordinates = None

    location = config["location"]
    lat = location.get("lat", None)
    long = location.get("lon", None)

    if lat and long:
        location_species = get_location_species(lat, long)
        coordinates = f"{lat},{long}"
    else:
        logger.warning("No location set, skipping location prediction")

    min_audio_confidence = config.get("min_audio_confidence") / 100
    min_location_confidence = config.get("min_location_confidence") / 100

    for filename in wav_files:
        recording_start, duration = filename.split(".")[0].split("_")
        logger.info(f"Analyzing recording {filename}")
        audio_path = recordings_dir / filename
        predictions = SpeciesPredictions(
            predict_species_within_audio_file(
                audio_path,
                min_confidence=min_audio_confidence,
                custom_model=DEFAULT_MODEL,
            )
        )

        logger.debug(predictions)

        detections = []

        for interval, result in predictions.items():
            for prediction, audio_confidence in result.items():
                scientific_name, common_name = prediction.split("_")

                if is_invalid_prediction(scientific_name):
                    logger.debug(f"SKIP: blacklisted prediction {prediction}")
                    continue

                loc_confidence = location_species.get(prediction, 0)
                if loc_confidence < min_location_confidence:
                    logger.debug(
                        f"SKIP: Expected min location score {min_location_confidence}, actual: {loc_confidence}"
                    )
                    continue

                detections.append(
                    {
                        "recording_start": datetime.fromtimestamp(
                            int(recording_start), tz=timezone.utc
                        ).isoformat(),
                        "recording_end": datetime.fromtimestamp(
                            int(recording_start) + int(duration), tz=timezone.utc
                        ).isoformat(),
                        "interval": f"{interval[0]},{interval[1]}",
                        "scientific_name": scientific_name,
                        "common_name": common_name,
                        "audio_confidence": float(audio_confidence),
                        "location_confidence": float(loc_confidence),
                        "location": coordinates,
                    }
                )

        if len(detections) > 0:
            res = session.post(
                "http://localhost:5000/api/detections",
                json=detections,
                headers={"X-CSRFToken": csrftoken},
                timeout=10,
            )
            res.raise_for_status()

            logger.info(
                f"Inserted {len(detections)} predictions for {filename} into the database."
            )

        os.remove(audio_path)
        logger.debug(f"Removed recording {filename} after analysis.")


if __name__ == "__main__":
    analyze()
