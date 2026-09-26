from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import AppVersion


def _version_tuple(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except (ValueError, AttributeError):
        return (0,)


class AppVersionView(APIView):
    """
    Majburiy yangilash tekshiruvi.
    So'rov: /api/core/app-version/?platform=android&current=1.0.0
    Javob: force_update=true bo'lsa ilova to'siq ekran ko'rsatadi.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        platform = request.query_params.get("platform", "android")
        current = request.query_params.get("current", "0.0.0")
        try:
            av = AppVersion.objects.get(platform=platform)
        except AppVersion.DoesNotExist:
            return Response({"force_update": False, "update_available": False})

        force = _version_tuple(current) < _version_tuple(av.min_version)
        available = _version_tuple(current) < _version_tuple(av.latest_version)

        # APK fayl yuklangan bo'lsa, uning to'liq manzili (store_url'dan ustun)
        apk_url = ""
        if av.apk_file:
            apk_url = request.build_absolute_uri(av.apk_file.url)

        return Response({
            "latest_version": av.latest_version,
            "min_version": av.min_version,
            "force_update": force,
            "update_available": available,
            "store_url": av.store_url,
            "apk_url": apk_url,
            "release_notes": av.release_notes,
        })


class SiteConfigView(APIView):
    """Umumiy sozlamalar — admin telefon raqami (do'kon egasi uchun)."""
    permission_classes = [AllowAny]

    def get(self, request):
        from .models import SiteConfig
        cfg = SiteConfig.get()
        return Response({
            "admin_phone": cfg.admin_phone,
            "admin_name": cfg.admin_name,
        })

class FeedbackView(APIView):
    """Do'kon egasidan fikr/taklif qabul qiladi (ilovadan yuboriladi)."""
    from rest_framework.permissions import IsAuthenticated
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import Feedback
        from accounts.models import Shop
        message = (request.data.get("message") or "").strip()
        if not message:
            return Response({"detail": "Fikr matni bo'sh."}, status=400)
        shop = Shop.objects.filter(owner=request.user).first()
        Feedback.objects.create(
            shop=shop,
            shop_name=shop.name if shop else "",
            phone=request.user.phone,
            message=message,
        )
        return Response({"detail": "Fikringiz uchun rahmat!"}, status=201)