from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.
from .models import *

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = CustomUser.objects.order_by('first_name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['subscription_category', 'access_number', 'start', 'end']

@admin.register(SubscriptionCategory)
class SubscriptionCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'default_access_number', 'duration', 'star_flag', 'sort']

@admin.register(SuperUserStatus)
class SuperUserStatusAdmin(admin.ModelAdmin):
    list_display = ['status']

@admin.register(SuperUserProfile)
class SuperUserProfileAdmin(admin.ModelAdmin):
    list_display = ['user']

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    pass
