import os
import uuid
import django
from django.db import connection
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), 'chatbot', '.env'))

# Initialize Django environment correctly (before model imports)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot.settings')
django.setup()

# Import models AFTER Django setup
from django.contrib.auth.models import User
from chat.models import UserProfile, ChatSession, ChatMessage

# Create test objects
user, _ = User.objects.get_or_create(username='test_encryption_user')
profile, _ = UserProfile.objects.get_or_create(user=user)
session, _ = ChatSession.objects.get_or_create(user_profile=profile, session_id=str(uuid.uuid4()))
test_msg = ChatMessage.objects.create(session=session, sender='user', content='Test encryption verification message')

# Fetch raw encrypted value from database
with connection.cursor() as cursor:
    cursor.execute('SELECT content FROM chat_chatmessage WHERE id = %s', [test_msg.id])
    raw_value = cursor.fetchone()[0]

# Verify encryption (Fernet-encrypted values start with 'gAAAAAB')
print(f"Raw encrypted value in database: {raw_value[:50]}...")
print(f"Encryption verified: {raw_value.startswith('gAAAAAB')}")