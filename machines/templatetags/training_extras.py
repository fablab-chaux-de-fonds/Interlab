from django import template
from ..models import Training

register = template.Library()


@register.filter
def price_format(price):
    nice_price = '%.2f' % price if price % 1 else int(price)
    return f'{nice_price} CHF'


@register.filter
def duration_format(duration):
    total_seconds = int(duration.total_seconds())

    hours = total_seconds // 3600
    s_hours = f'{hours}h' if hours else ''

    minutes = (total_seconds % 3600) // 60
    s_minutes = str(minutes) if minutes else ''
    if not hours:
        s_minutes = f'{s_minutes} min'

    return f'{s_hours}{s_minutes}'


@register.filter
def level_format(lvl):
    return dict(Training.LEVEL_CHOICES)[lvl]
