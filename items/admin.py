from django.contrib import admin
from .models import LostItem, FoundItem, ItemMatch, Notification, FoundItemView

@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'reporter', 'category', 'location_lost', 'date_lost', 'status', 'created_at']
    list_filter = ['status', 'category', 'location_lost']
    search_fields = ['title', 'description', 'reporter__username']

@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'finder', 'category', 'location_found', 'date_found', 'status']
    list_filter = ['status', 'category', 'location_found']
    search_fields = ['title', 'public_description', 'private_description']

@admin.register(ItemMatch)
class ItemMatchAdmin(admin.ModelAdmin):
    list_display = ['lost_item', 'found_item', 'match_score', 'status', 'fraud_risk', 'created_at']
    list_filter = ['status', 'fraud_risk']

@admin.register(FoundItemView)
class FoundItemViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'found_item', 'viewed_at']
    list_filter = ['viewed_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
