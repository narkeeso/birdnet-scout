import arrow
from flask import Flask


def percentage_filter(value: float | None) -> str:
    """
    Converts a float/decimal number to a percentage string
    """
    if value is None:
        return "0%"

    return f"{value * 100:.0f}%"


def date_humanize(value: str) -> str:
    """
    Convert UTC timestamp to human-readable relative time in local timezone.
    Designed for use as a Jinja template filter.

    Args:
        value: UTC timestamp string to convert

    Returns:
        Humanized relative time string (e.g. "2 hours ago")
    """
    utc = arrow.get(value)
    local = utc.to("local")
    return local.humanize()


def register(app: Flask):
    app.jinja_env.filters["percentage"] = percentage_filter
    app.jinja_env.filters["humanize"] = date_humanize
