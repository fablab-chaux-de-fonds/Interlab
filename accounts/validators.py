import re
import dns.resolver

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_special_characters(value):
    if not re.fullmatch(r'[\w]+', value, re.UNICODE):
        raise ValidationError(_("Special characters are not allowed."))

def validate_domain(value):
    try:
        dns.resolver.resolve(value.split('@')[1], 'MX')
    except dns.resolver.NXDOMAIN as exception:
        raise ValidationError(_('This domain is not valid')) from exception
        