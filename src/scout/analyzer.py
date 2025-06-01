"""Analyze audio recordings using BirdNET and store predictions in a database."""

import fnmatch
import sqlite3
import os
from datetime import datetime
from pathlib import Path

from birdnet import SpeciesPredictions, predict_species_within_audio_file  # type: ignore
from loguru import logger

recordings_dir = Path("recordings")
recordings_dir.mkdir(exist_ok=True)

PREDICTION_BLACKLIST = ["Dog_", "Human ", "Engine_", "Gun_"]


def is_invalid_prediction(prediction: str) -> bool:
    """
    Check if the prediction is invalid (in the blacklist).
    """
    return any(prediction.startswith(blacklist) for blacklist in PREDICTION_BLACKLIST)


def within_confidence_threshold(confidence: float) -> bool:
    """
    Check if the confidence level is above the threshold.
    """
    return confidence > 0.4


def analyze(db: sqlite3.Connection):
    """
    Analyze audio recordings in the recordings directory and store predictions in the database.
    """

    wav_files = [f for f in os.listdir(recordings_dir) if fnmatch.fnmatch(f, "*.wav")]

    logger.debug(f"Found {len(wav_files)} recordings to analyze.")

    cursor = db.cursor()

    for filename in wav_files:
        logger.debug("Analyzing recording {filename}")
        audio_path = recordings_dir / filename
        predictions = SpeciesPredictions(predict_species_within_audio_file(audio_path))

        count = 0
        for interval, result in predictions.items():
            for prediction, confidence in result.items():
                if not within_confidence_threshold(confidence):
                    logger.debug(
                        f"Skipping low confidence prediction: {prediction} ({confidence})"
                    )
                    continue

                if is_invalid_prediction(prediction):
                    logger.debug(f"Skipping blacklisted prediction: {prediction}")
                    continue

                cursor.execute(
                    """
                    INSERT INTO predictions (recording_key, interval, prediction, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        filename,
                        f"{interval[0]},{interval[1]}",
                        prediction,
                        float(confidence),
                        datetime.now().isoformat(),
                    ),
                )
                count += 1

        db.commit()
        logger.info(f"Inserted {count} predictions for {filename} into the database.")

        os.remove(audio_path)
        logger.debug(f"Removed recording {filename} after analysis.")
