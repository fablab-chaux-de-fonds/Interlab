from django.core.exceptions import ValidationError
from django.apps import apps
from django.shortcuts import render
import requests
import sys

from .forms import RegisterForm
from .apps import NewsletterConfig

def register(request):
    """This action handle newsletter registering email"""
    form = None
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        form.success = False
        if form.is_valid():
            try:
                response = register_email(form.cleaned_data['email'])    
                if response['result'] != 'success':
                    form.add_error('email', ValidationError('Registration refused', 'registration_refused'))
                else:
                    form.fields['email'].initial = form.cleaned_data['email']
                    form.success = True
            except Exception as e:
                print(e, file=sys.stderr)
                form.add_error('email', ValidationError('Registration failed, try again later', 'http_error'))
    if not form:
        form = RegisterForm()
    return render(request, 'forms/newsletter.html', {'form': form })

def register_email(email):
    """Utility method to register email in configured mailing list newsletter"""
    app = apps.get_app_config(NewsletterConfig.name)
    resp = requests.post(url=app.newsletter_url_importcontact(), auth=app.newsletter_auth(), json={'contacts':[{'email':email}]})
    resp.raise_for_status()
    return resp.json()

def get_contact():
    """Utility to get contact in configured mailing list newsletter"""
    app = apps.get_app_config(NewsletterConfig.name)
    resp = requests.get(url=app.newsletter_url_getcontact(), auth=app.newsletter_auth())
    resp.raise_for_status()
    return resp.json()

def update_contact(id, email):
    """Utility method to update email in configured mailing list newsletter"""
    app = apps.get_app_config(NewsletterConfig.name)
    resp = requests.put(url=app.newsletter_url_updatecontact(id), auth=app.newsletter_auth(), json={'email':email})
    resp.raise_for_status()

    return resp.json()