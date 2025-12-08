from django.core.management.base import BaseCommand
from django.db.models import Count
from chat.models import ChatSession

class Command(BaseCommand):
    help = 'Remove all empty chat sessions (sessions with no messages)'

    def handle(self, *args, **options):
        # Find sessions with no messages
        empty_sessions = ChatSession.objects.annotate(
            message_count=Count('messages')
        ).filter(message_count=0)

        count = empty_sessions.count()

        if count > 0:
            empty_sessions.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count} empty chat sessions')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No empty chat sessions found')
            )
