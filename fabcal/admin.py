from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(OpeningSlot)
class OpeningSlotAdmin(admin.ModelAdmin):
    list_display = ['opening', 'start', 'end', 'user']

@admin.register(EventSlot)
class EventSlotAdmin(admin.ModelAdmin):
    list_display = ['event', 'start', 'end', 'user', 'is_active', 'registration_required']

@admin.register(TrainingSlot)
class TrainingSlotAdmin(admin.ModelAdmin):
    list_display = ['training', 'start', 'end', 'user']
    filter_horizontal = ['registrations']

@admin.register(MachineSlot)
class MachineSlotAdmin(admin.ModelAdmin):
    list_display = ['machine', 'opening_slot', 'start', 'end', 'user']