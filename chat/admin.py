from django.contrib import admin
from .models import UserProfile, ChatSession, ChatMessage, BotConfiguration, FAQ, SensitiveData

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'session_id', 'start_time', 'end_time')
    list_filter = ('start_time',)
    search_fields = ('user_profile__user__username', 'session_id')
    date_hierarchy = 'start_time'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender', 'timestamp', 'content')
    list_filter = ('sender', 'timestamp')
    search_fields = ('session__session_id', 'content')
    date_hierarchy = 'timestamp'

@admin.register(BotConfiguration)
class BotConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'keywords', 'created_at', 'updated_at')
    search_fields = ('question', 'keywords', 'answer')
    list_filter = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('question', 'answer', 'keywords')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SensitiveData)
class SensitiveDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'sensitive_info', 'created_at')