from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(Profile)
class AccountsAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['subscription_category', 'access_number', 'start', 'end']

@admin.register(SubscriptionCategory)
class SubscriptionCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'default_access_number', 'duration', 'star_flag', 'sort']
