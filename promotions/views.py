from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny
from .models import Banner, PromoScreen
from .serializers import BannerSerializer, PromoScreenSerializer


class BannerViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Bosh sahifa bannerlari (faol va muddati o'tmaganlari)."""
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        now = timezone.now()
        return Banner.objects.filter(is_active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))


class PromoScreenViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Splash/interstitial reklama. ?placement=after_login."""
    serializer_class = PromoScreenSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        now = timezone.now()
        qs = PromoScreen.objects.filter(is_active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now)
        ).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        placement = self.request.query_params.get("placement")
        return qs.filter(placement=placement) if placement else qs
