from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'price', 'machine_category', 'level', 'duration', 'photo']

@admin.register(MachineCategory)
class MachineCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(OutcomeListItem)
class TrainingOutcomeAdmin(admin.ModelAdmin):
    list_display = ['training', 'description']

@admin.register(DIYListItem)
class TrainingDIYAdmin(admin.ModelAdmin):
    list_display = ['training', 'title', 'name', 'url']

@admin.register(Faq)
class TrainingFaqAdmin(admin.ModelAdmin):
    list_display = ['about', 'question', 'answer']

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'price', 'category', 'photo']

@admin.register(MachineGroup)
class MachineGroupAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'sort']
