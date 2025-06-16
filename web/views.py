import json

import requests
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.forms.models import model_to_dict
from django.views.generic.base import TemplateView

from . import models


class HomeView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = models.Config.config.get_config()
        detections = models.Detection.detections.get_valid(config)
        context["detections"] = detections
        total_discovered = models.Detection.detections.get_discovered(config).count()
        context["total_discovered"] = total_discovered
        return context


class DetectionsView(TemplateView):
    template_name = "detections.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = models.Config.config.get_config()
        context["detections"] = models.Detection.detections.get_valid(config)
        context["total_discovered"] = models.Detection.detections.get_discovered(
            config
        ).count()
        return context


class SettingsView(TemplateView):
    template_name = "settings.html"


def healthcheck(request):
    return HttpResponse(status=204)


@ensure_csrf_cookie
def get_config(request):
    if request.method == "GET":
        config = models.Config.config.get_config()
        payload = model_to_dict(config)
        return JsonResponse(payload)
    return HttpResponse(status=405)


def create_detections(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            if not isinstance(data, list):
                return JsonResponse(
                    {"error": "Expected array of detections"}, status=400
                )

            detections = []
            for item in data:
                try:
                    detections.append(
                        models.Detection(
                            recording_start=item["recording_start"],
                            recording_end=item["recording_end"],
                            interval=item["interval"],
                            scientific_name=item["scientific_name"],
                            common_name=item["common_name"],
                            audio_confidence=item["audio_confidence"],
                            location_confidence=item["location_confidence"],
                            location=item["location"],
                        )
                    )
                except KeyError as e:
                    return JsonResponse(
                        {"error": f"Missing required field: {str(e)}"}, status=400
                    )

            models.Detection.detections.bulk_create(detections)
            return HttpResponse(status=204)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
    return HttpResponse(status=405)  # Method Not Allowed


def update_location(request: HttpRequest):
    session = requests.Session()
    response = session.get("https://api.ipify.org", timeout=5)
    ip_address = response.text
    response = session.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
    data = response.json()
    models.Config.config.update(id=1, location=data)
    return HttpResponse(status=204, headers={"HX-Refresh": "true"})
