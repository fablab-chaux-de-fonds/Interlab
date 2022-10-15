from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'price', 'machine_category', 'level', 'duration', 'photo']

@admin.register(MachineCategory)
class MachineCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(Faq)
class TrainingFaqAdmin(admin.ModelAdmin):
    list_display = ['about', 'question', 'answer']

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'price', 'category', 'photo']

@admin.register(MachineGroup)
class MachineGroupAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'sort']

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'link', 'icon']

@admin.register(ToolTraining)
class ToolTraining(admin.ModelAdmin):
    list_display = ['training', 'sort', 'tool']

@admin.register(ToolMachine)
class ToolMachine(admin.ModelAdmin):
    list_display = ['machine', 'sort', 'tool']