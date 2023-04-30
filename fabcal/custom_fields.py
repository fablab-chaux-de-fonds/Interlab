import datetime
import dateparser
from django import forms

class CustomDateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        input_formats = ['%d %B %Y', '%d %b %Y']
        kwargs['input_formats'] = input_formats
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value is None:
            return None

        if isinstance(value, datetime.date):
            return value

        if isinstance(value, str):
            value = value.strip()

        if not value:
            return None

        return dateparser.parse(value)