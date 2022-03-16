from celery import shared_task
from django.apps import apps
import requests

from .apps import NewsletterConfig

@shared_task
def register_email(email):
    """Utility method to register email in configured mailing list newsletter"""
    app = apps.get_app_config(NewsletterConfig.name)
    resp = requests.post(url=app.newsletter_url_importcontact(), auth=app.newsletter_auth(), json={'contacts':[{'email':email}]})
    resp.raise_for_status()
    return resp.json()