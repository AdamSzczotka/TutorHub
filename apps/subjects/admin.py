from django.contrib import admin

from .models import Level, Subject, SubjectLevel


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'order_index', 'color']
    ordering = ['order_index']


@admin.register(SubjectLevel)
class SubjectLevelAdmin(admin.ModelAdmin):
    list_display = ['subject', 'level']
    list_filter = ['subject', 'level']
