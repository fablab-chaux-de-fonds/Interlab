from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['title', 'desc', 'full_price', 'machine_category', 'level', 'duration', 'photo']

@admin.register(TrainingValidation)
class TrainingValidationAdmin(admin.ModelAdmin):
    list_display = ['training', 'profile', 'created_date', 'modified_date']

@admin.register(Faq)
class TrainingFaqAdmin(admin.ModelAdmin):
    list_display = ['about', 'question', 'answer']

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['title', 'desc', 'full_price', 'premium_price', 'category', 'photo']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'link', 'icon']

@admin.register(ToolTraining)
class ToolTrainingAdmin(admin.ModelAdmin):
    list_display = ['training', 'sort', 'card']

@admin.register(ToolMachine)
class ToolMachineAdmin(admin.ModelAdmin):
    list_display = ['machine', 'sort', 'card']

@admin.register(HighlightMachine)
class HighlightMachineAdmin(admin.ModelAdmin):
    list_display = ['machine', 'sort', 'card']

class AbstractMachinesFilterAdmin(admin.ModelAdmin):
    list_display = ['name', 'sort']
    ordering = ['sort']
@admin.register(MachineCategory)
class MachineCategoryAdmin(AbstractMachinesFilterAdmin):
    list_display = ['name', 'sort']
@admin.register(MachineGroup)
class MachineGroupAdmin(AbstractMachinesFilterAdmin):
    list_display = ['name', 'sort']
@admin.register(Material)
class MaterialAdmin(AbstractMachinesFilterAdmin):
    list_display = ['name', 'sort']

@admin.register(Workshop)
class WorkshopAdmin(AbstractMachinesFilterAdmin):
    list_display = ['name', 'sort']

