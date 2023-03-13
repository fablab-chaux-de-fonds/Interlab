import re

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

def validate_special_characters(value):
    if re.search('[^a-zA-Z0-9]+', value):
        raise ValidationError(_("Special characters are not allowed."))