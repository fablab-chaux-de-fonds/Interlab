from django import template
from django.conf import settings
from django.db.models.expressions import F


register = template.Library() 

@register.filter(name='has_group') 
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter
def get_list(dictionary, key):
    return [int(i) for i in dictionary.getlist(key)]

@register.filter
def filter_machine(obj, machine):
    return obj.filter(machine=machine).order_by('start')

@register.filter
def filter_slot_minimum_time(obj):
    return [i for i in obj if i.get_duration >=settings.FABCAL_MINIMUM_RESERVATION_TIME]

@register.filter
def filter_user(obj):
    return obj.filter(user__isnull=True)

@register.filter
def get_type(value):
    return value.__class__.__name__
