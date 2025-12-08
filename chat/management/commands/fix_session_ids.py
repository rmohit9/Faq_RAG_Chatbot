import uuid
from django.core.management.base import BaseCommand
from chat.models import ChatSession

class Command(BaseCommand):
    help = 'Fix invalid session IDs for ChatSession records'

    def handle(self, *args, **options):
        sessions = ChatSession.objects.values('id', 'session_id')
        for s in sessions:
            try:
                uuid.UUID(str(s['session_id']))
            except:
                session_obj = ChatSession.objects.get(id=s['id'])
                session_obj.session_id = uuid.uuid4()
                session_obj.save()
