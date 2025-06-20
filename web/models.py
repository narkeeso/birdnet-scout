from typing import Dict, List
from dateutil.tz import tzlocal

import arrow
from django.db import models
from django.db.models import Avg, Count, Max
from django.db.models.functions import TruncDate
from django.utils import timezone


class ConfigManager(models.Manager):
    def get_config(self):
        config, _ = models.QuerySet["Config"](self.model, using=self._db).get_or_create(
            id=1,
            defaults={
                "location": {},
                "min_location_confidence": 1,
                "min_audio_confidence": 70,
                "min_sample_threshold": 2,
                "timezone": "US/Pacific",
            },
        )
        return config


class Config(models.Model):
    location = models.JSONField()
    min_audio_confidence = models.SmallIntegerField()
    min_location_confidence = models.SmallIntegerField()
    min_sample_threshold = models.SmallIntegerField()
    timezone = models.CharField(default="US/Pacific")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    config = ConfigManager()


class DetectionQuerySet(models.QuerySet["Detection"]):
    def get_valid(self, config: Config):
        timezone.activate(tzlocal())

        return (
            self.annotate(date=TruncDate("recording_start"))
            .values("scientific_name", "common_name", "date")
            .annotate(
                sample_count=Count("scientific_name"),
                audio_confidence=Avg("audio_confidence"),
                location_confidence=Max("location_confidence"),
                last_detected_at=Max("recording_start"),
            )
            .filter(sample_count__gte=config.min_sample_threshold)
            .order_by("-last_detected_at")
        )

    def get_discovered(self, config: Config):
        return (
            self.values("scientific_name")
            .annotate(count=Count("scientific_name"))
            .filter(count__gte=config.min_sample_threshold)
        )


class DetectionManager(models.Manager):
    def get_queryset(self):
        return DetectionQuerySet(self.model, using=self._db)

    def get_valid(self, config: "Config"):
        results = self.get_queryset().get_valid(config)
        detections: Dict[str, List] = {}
        for row in results:
            created_at = arrow.get(row.get("date", ""))
            date = created_at.to("local").format("YYYY-MM-DD")

            if detections.get(date) is None:
                detections[date] = []

            name_slug = row.get("common_name", "").replace("'", "").replace(" ", "_")
            row["link"] = f"https://www.allaboutbirds.org/guide/{name_slug}"

            detections[date].append(row)
        return detections

    def get_discovered(self, config: "Config"):
        return self.get_queryset().get_discovered(config)


class Detection(models.Model):
    recording_start = models.DateTimeField()
    recording_end = models.DateTimeField()
    interval = models.CharField(max_length=50)
    scientific_name = models.CharField(max_length=200)
    common_name = models.CharField(max_length=200)
    audio_confidence = models.FloatField()
    location_confidence = models.FloatField()
    location = models.CharField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    detections = DetectionManager()
