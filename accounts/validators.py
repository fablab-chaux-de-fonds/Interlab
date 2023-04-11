import re
import whois

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

def validate_special_characters(value):
    if re.search('[^a-zA-Z0-9]+', value):
        raise ValidationError(_("Special characters are not allowed."))

def validate_domain(value):
    try:
        if whois.whois(value.split('@')[1]).domain_name is None:
            raise ValidationError(_('This domain is not valid'))

    except whois.parser.PywhoisError as exception:
        raise ValidationError(_('This domain is not valid')) from exception
        