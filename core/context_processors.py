"""Dashboard statistikasini har bir admin sahifasiga uzatadi."""
from .admin_dashboard import get_dashboard_stats


def dashboard(request):
    # Faqat admin bosh sahifasida hisoblaymiz (tejamkorlik uchun)
    if request.path == "/admin/" and request.user.is_authenticated:
        try:
            return {"dashboard_stats": get_dashboard_stats()}
        except Exception:
            return {}
    return {}
