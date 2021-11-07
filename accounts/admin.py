from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(Profile)
class AccountsAdmin(admin.ModelAdmin):
    list_display = ['user', 'active', 'subscription']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['category', 'start', 'end']

@admin.register(SubscriptionCategory)
class SubscriptionCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'access_number', 'duration', 'star_flag', 'sort']
