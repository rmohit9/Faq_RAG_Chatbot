from django.conf import settings

def social_links(request):
    return {
        "social": settings.SOCIAL_LINKS
    }