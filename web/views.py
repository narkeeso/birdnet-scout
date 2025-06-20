import json

import arrow
from loguru import logger
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.forms.models import model_to_dict
from django.views.generic.base import TemplateView
from django.shortcuts import redirect

from . import models, forms, services


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = models.Config.config.get_config()
        context["config_form"] = forms.SettingsForm(
            data={
                "min_location_confidence": config.min_location_confidence,
                "min_audio_confidence": config.min_audio_confidence,
            }
        )
        return context

    def post(self, request: HttpRequest):
        config = models.Config.config.get(pk=1)
        form = forms.SettingsForm(request.POST)

        if form.is_valid():
            config.min_audio_confidence = form.cleaned_data["min_audio_confidence"]
            config.min_location_confidence = form.cleaned_data[
                "min_location_confidence"
            ]
            config.save()
            return redirect("settings-view")

        context = self.get_context_data()
        context["config_form"] = form
        return self.render_to_response(context)


service_state = {
    "analyzer": arrow.now().timestamp(),
    "recorder": arrow.now().timestamp(),
}


def analyzer_heartbeat(request: HttpRequest):
    if request.method == "GET":
        service_state["analyzer"] = arrow.now().timestamp()
    return HttpResponse(status=204)


def recorder_heartbeat(request: HttpRequest):
    if request.method == "GET":
        service_state["recorder"] = arrow.now().timestamp()
    return HttpResponse(status=204)


class HealthcheckView(TemplateView):
    template_name = "partials/healthcheck.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = arrow.now().timestamp()
        healthcheck = {
            "recorder": not (now - service_state["recorder"] > 30),
            "analyzer": not (now - service_state["analyzer"] > 30),
        }
        context = {"healthcheck": healthcheck}

        return context


@ensure_csrf_cookie
def get_config(request):
    if request.method == "GET":
        config = models.Config.config.get_config()

        # Best attempt to update location
        try:
            services.update_location(config)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception(e)

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
