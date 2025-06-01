from pathlib import Path
from time import time

import scipy.io.wavfile as wavfile  # type: ignore
import sounddevice as sd  # type: ignore
from loguru import logger

recordings_dir = Path("recordings")
recordings_dir.mkdir(exist_ok=True)


def record():
    # Store the epoch start timestamp
    duration = 60  # seconds
    recording = sd.rec(int(duration * 44100), samplerate=44100, channels=1)

    logger.debug(f"Recording for {duration} seconds to {sd.default.device}")

    start_timestamp = time()
    sd.wait()
    end_timestamp = time()

    recording_key = f"{recordings_dir}/{int(start_timestamp)}_{int(end_timestamp)}.wav"

    wavfile.write(recording_key, 44100, recording)
    logger.debug(f"Recording saved to {recording_key}")
