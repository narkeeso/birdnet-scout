"""
This is the main entry point for the Scout application that starts the
recorder and analyzer processes.
"""

import os
import time
from multiprocessing import Process

from loguru import logger

from . import analyzer, recorder


env = os.getenv("ENVIRONMENT", "development")


def recorder_task():
    """Start the audio recorder process."""
    logger.info("Starting recorder process...")
    while True:
        recorder.record()


def analyzer_task():
    """Start the audio analyzer process."""
    logger.info("Starting analyzer process...")
    while True:
        analyzer.analyze()
        time.sleep(2)


p1 = Process(target=recorder_task)
p2 = Process(target=analyzer_task)

p1.start()
p2.start()

try:
    p1.join()
    p2.join()
except KeyboardInterrupt:
    p1.terminate()
    p2.terminate()
