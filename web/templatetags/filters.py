import arrow
from django import template


register = template.Library()


@register.filter
def percentage(value: float | None) -> str:
    """
    Converts a float/decimal number to a percentage string
    """
    if value is None:
        return "0%"

    return f"{value * 100:.0f}%"


@register.filter
def humanize(value: str) -> str:
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
