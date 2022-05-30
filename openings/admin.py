from django.contrib import admin

# Register your models here.
# Register your models here.
from .models import *

@admin.register(Opening)
class OpeningAdmin(admin.ModelAdmin):
    list_display = ["title", "is_open_to_reservation", "is_open_to_questions", "is_reservation_mandatory"]
        
    