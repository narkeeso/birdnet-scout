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


def analyze(db: sqlite3.Connection):
    # Find all recordings in the recordings directory
    wav_files = [f for f in os.listdir(recordings_dir) if fnmatch.fnmatch(f, "*.wav")]

    logger.debug(f"Found {len(wav_files)} recordings to analyze.")

    cursor = db.cursor()

    # Print the filenames
    for filename in wav_files:
        logger.debug("Analyzing recording {filename}")
        audio_path = recordings_dir / filename
        predictions = SpeciesPredictions(predict_species_within_audio_file(audio_path))

        for interval, result in predictions.items():
            for prediction, confidence in result.items():
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

        db.commit()

        os.remove(audio_path)
        logger.debug(f"Processed {filename} and removed from disk.")
