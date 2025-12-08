# c:/Users/patel/sheryansh/final/chatbot/chat/models.py
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta # Import timedelta for DurationField default
from .fields import EncryptedTextField # Import the custom encrypted field

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bot_personality = EncryptedTextField(default='Friendly')
    chats_initiated = models.IntegerField(default=0)
    total_chat_time = models.DurationField(default=timedelta)
    custom_bots = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username

class ChatSession(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.CharField(max_length=36, unique=True, editable=False) # Temporarily CharField to fix invalid UUIDs
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.session_id} for {self.user_profile.user.username}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10) # 'user' or 'bot'
    content = EncryptedTextField() # Changed to EncryptedTextField
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender} in {self.session.session_id}: {self.content[:50]}"

class BotConfiguration(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    prompt_template = models.TextField(blank=True, null=True) # For defining bot's persona/instructions
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class FAQ(models.Model):
    question = models.TextField(unique=True)
    answer = EncryptedTextField()
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for semantic matching (e.g., 'account,login,access')")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def get_keywords_list(self):
        """Return list of lowercase keywords without whitespace"""
        if not self.keywords:
            return []
        return [kw.strip().lower() for kw in self.keywords.split(',')]

    def __str__(self):
        return self.question[:50]

# Example model for sensitive data (already created)
class SensitiveData(models.Model):
    name = models.CharField(max_length=100)
    sensitive_info = EncryptedTextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name