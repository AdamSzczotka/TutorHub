from .services import AnnouncementService


def announcements(request):
    """Context processor to add active announcements to all templates."""
    if request.user.is_authenticated:
        return {
            'announcements': AnnouncementService.get_active_announcements(request.user)
        }
    return {'announcements': []}
