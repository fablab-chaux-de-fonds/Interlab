from django.db import models
from cms.models.pluginmodel import CMSPlugin

class TypewriterPlugin(CMSPlugin):
    strings = models.TextField("Strings", help_text="Enter the strings for the typewriter effect, separated by commas.")
