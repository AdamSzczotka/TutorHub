from django.contrib import admin

from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'location', 'is_active', 'is_virtual']
    list_filter = ['is_active', 'is_virtual']
    search_fields = ['name', 'location']
