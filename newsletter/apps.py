from django.apps import AppConfig
import os
import requests
from requests.auth import HTTPBasicAuth

NEWSLETTER_URL = os.environ.get('NEWSLETTER_URL')
NEWSLETTER_USER = os.environ.get('NEWSLETTER_USER')
NEWSLETTER_SECRET = os.environ.get('NEWSLETTER_SECRET')
NEWSLETTER_LIST_NAME = os.environ.get('NEWSLETTER_LIST_NAME')

class NewsletterConfig(AppConfig):
    name = 'newsletter'

    def __init__(self, app_name, app_module):
        super(NewsletterConfig, self).__init__(app_name, app_module)
        self.newsletter_list_id = None

    def ready(self):
        try:
            response = requests.get(url=NEWSLETTER_URL, auth=self.newsletter_auth())
            response.raise_for_status()
            self.newsletter_list_id = next(i['id'] for i in response.json()['data']['data'] if i['name'] == NEWSLETTER_LIST_NAME)
        except Exception as e:
            print(e)

    def newsletter_url_importcontact(self):
        return '{0}/{1}/importcontact'.format(NEWSLETTER_URL, self.newsletter_list_id)

    def newsletter_auth(self):  
        return HTTPBasicAuth(NEWSLETTER_USER, NEWSLETTER_SECRET)

