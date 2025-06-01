"""
This is the main entry point for the Outpost application that starts the
recorder and analyzer processes.
"""

import sqlite3
import time
from multiprocessing import Process

from loguru import logger

from . import analyzer, recorder


def start_recorder():
    """Start the audio recorder process."""
    logger.debug("Starting audio recorder...")

    while True:
        recorder.record()


def start_analyzer():
    """Start the audio analyzer process."""
    logger.debug("Starting audio analyzer...")

    db = sqlite3.connect("birdnet.db")
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            recording_key TEXT,
            interval TEXT,
            prediction TEXT,
            confidence REAL,
            created_at TIMESTAMP
        )
        """
    )
    db.commit()

    while True:
        analyzer.analyze(db)
        time.sleep(30)


w1 = Process(target=start_recorder)
w2 = Process(target=start_analyzer)

w1.start()
w2.start()

try:
    while True:
        pass
except KeyboardInterrupt:
    w1.terminate()
    w2.terminate()

    w1.join()
    w2.join()
