from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(OpeningSlot)
class OpeningSlotAdmin(admin.ModelAdmin):
    list_display = ['opening', 'start', 'end', 'user']
