"""
Module for recording audio using arecord and saving it as a WAV file.
"""

import os
import shutil
from pathlib import Path
from time import time
import subprocess
from loguru import logger

recordings_dir = Path("recordings")
recordings_dir.mkdir(exist_ok=True)


def record():
    """
    Record audio for a specified duration and save it to a file in the recordings directory.
    """
    duration = 12  # seconds
    start_timestamp = time()

    # Create the recording key based on the start timestamp
    recording_key = f"{recordings_dir}/{int(start_timestamp)}_{duration}.wav"

    logger.debug(f"Recording for {duration} seconds")

    # Use arecord to record directly to WAV file
    subprocess.run(
        [
            "arecord",
            "-d",
            str(duration),
            "-f",
            "cd",
            "-c",
            "1",
            "-r",
            "44100",
            f"/tmp/birdnet/{recording_key}",
        ],
        check=True,
    )

    shutil.move(f"/tmp/birdnet/{recording_key}", recording_key)

    logger.debug(f"Recording saved to {recording_key}")


if __name__ == "__main__":
    logger.info("Starting recorder process...")

    # Store in progres recordings here
    os.makedirs("/tmp/birdnet/recordings", exist_ok=True)

    while True:
        record()
