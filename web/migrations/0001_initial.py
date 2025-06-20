# Generated by Django 5.2.3 on 2025-06-15 05:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Config",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("location", models.JSONField()),
                ("min_sample_threshold", models.SmallIntegerField()),
                ("min_audio_confidence", models.SmallIntegerField()),
                ("min_location_confidence", models.SmallIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Detection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("recording_start", models.DateTimeField()),
                ("recording_end", models.DateTimeField()),
                ("interval", models.CharField(max_length=50)),
                ("scientific_name", models.CharField(max_length=200)),
                ("common_name", models.CharField(max_length=200)),
                ("audio_confidence", models.FloatField()),
                ("location_confidence", models.FloatField()),
                ("location", models.CharField(null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
