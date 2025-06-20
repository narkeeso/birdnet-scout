from django import forms


class SettingsForm(forms.Form):
    min_audio_confidence = forms.IntegerField(
        initial=70,
        max_value=90,
        min_value=0,
        label="Min Audio Score",
        help_text="0-90 valid; Recommend at least 70 for better predictions",
    )
    min_location_confidence = forms.IntegerField(
        initial=1,
        max_value=90,
        min_value=0,
        label="Min Location Score",
        help_text="0-90 valid; Recommend at least 1 for better predictions",
    )
