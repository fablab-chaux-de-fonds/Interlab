from django import template

register = template.Library() 

@register.filter(name='get_item') 
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def can_unregister(object, user):
    return user in object.get_reservation_list and object.is_editable

@register.filter
def cannot_unregister(object, user):
    return user in object.get_reservation_list and not object.is_editable

@register.filter
def is_registered(object, user):
    return user in object.get_reservation_list

@register.filter
def registration_disabled(object):
    return object.available_registration <= 0

@register.filter
def no_registration_limit(object):
    return object.registration_limit == 0

@register.filter
def is_onsite(object):
    return object.registration_type == 'onsite'