from django.urls import path

from . import views

urlpatterns = [
    # Views
    path("", views.HomeView.as_view(), name="home-view"),
    path("views/detections", views.DetectionsView.as_view(), name="detections-view"),
    path("views/settings", views.SettingsView.as_view(), name="settings-view"),
    # API Routes
    path("healthcheck", views.HealthcheckView.as_view(), name="healthcheck"),
    path("heartbeat/recorder", views.recorder_heartbeat),
    path("heartbeat/analzyer", views.analyzer_heartbeat),
    path("api/config", views.get_config),
    path("api/detections", views.create_detections),
]
