from datetime import datetime

import dataset

db = dataset.connect("sqlite:///scout.db")


def get_latest_birds():
    result = db.query(
        """
        SELECT
            COUNT(scientific_name) AS sample_count,
            common_name,
            scientific_name,
            AVG(audio_confidence) AS audio_confidence,
            MAX(location_confidence) AS location_confidence,
            location AS location,
            MAX(recording_start) AS created_at
        FROM detections
        GROUP BY scientific_name, common_name, location, DATE(recording_start)
        HAVING COUNT(scientific_name) > 3
        ORDER BY created_at DESC
        """
    )

    results = {}

    for row in result:
        if not row:
            return

        date = datetime.fromisoformat(row.get("created_at", "")).strftime("%Y-%m-%d")

        if results.get(date) is None:
            results[date] = []
        else:
            results[date].append(row)

    return results


def get_total_discovered() -> int:
    result = db.query(
        """
        SELECT DISTINCT scientific_name FROM detections GROUP BY scientific_name HAVING COUNT(scientific_name) > 3;
        """
    )

    count = 0

    for r in result:
        count += 1

    return count
