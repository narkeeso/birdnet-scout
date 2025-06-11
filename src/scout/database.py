from datetime import datetime

import dataset

db = dataset.connect("sqlite:///scout.db")


def create_table_detections():
    db.query(
        """
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_start TEXT,
            recording_end TEXT,
            interval TEXT,
            scientific_name TEXT,
            common_name TEXT,
            audio_confidence REAL,
            location_confidence REAL,
            location TEXT,
            created_at TEXT
        )
        """
    )
