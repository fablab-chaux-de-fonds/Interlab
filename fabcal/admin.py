from django.contrib import admin

# Register your models here.
from .models import *
from accounts.models import CustomUser

@admin.register(OpeningSlot)
class OpeningSlotAdmin(admin.ModelAdmin):
    list_display = ['opening', 'start', 'end', 'user']
    search_fields = ["user__first_name"]
    ordering = ['-start']

@admin.register(EventSlot)
class EventSlotAdmin(admin.ModelAdmin):
    list_display = ['event', 'start', 'end', 'user', 'is_active', 'registration_required']

@admin.register(RegistrationEventSlot)
class RegistrationEventSlotAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_slot', 'registration_date', 'number_of_attendees')
    search_fields = ('user__first_name', 'user__last_name', 'event_slot__name')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = CustomUser.objects.order_by('first_name')
        if db_field.name == "event_slot":
            kwargs["queryset"] = EventSlot.objects.order_by('-start')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(TrainingSlot)
class TrainingSlotAdmin(admin.ModelAdmin):
    list_display = ['training', 'start', 'end', 'user']
    filter_horizontal = ['registrations']

@admin.register(MachineSlot)
class MachineSlotAdmin(admin.ModelAdmin):
    list_display = ['machine', 'opening_slot', 'start', 'end', 'user']
    search_fields = ["machine__title", "user__first_name"]
    list_filter = ["machine"]
    ordering = ['-start']