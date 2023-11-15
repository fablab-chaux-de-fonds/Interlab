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
    list_display = ['about', 'question', 'answer', 'sort']

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'full_price', 'premium_price']

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
    pass
@admin.register(MachineGroup)
class MachineGroupAdmin(AbstractMachinesFilterAdmin):
    pass
@admin.register(Material)
class MaterialAdmin(AbstractMachinesFilterAdmin):
    pass

@admin.register(Workshop)
class WorkshopAdmin(AbstractMachinesFilterAdmin):
    pass

@admin.register(Specification)
class SpecificationAdmin(AbstractMachinesFilterAdmin):
    list_display = ['key', 'value', 'machine', 'sort']

@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ['title']

@admin.register(TrainingNotification)
class TrainingNotificationAdmin(admin.ModelAdmin):
    list_display = ['training', 'profile', 'created_date']