from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Region, District, Shop
from .serializers import (
    RegionSerializer, DistrictSerializer, ShopSerializer, RegisterSerializer,
)


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.filter(is_active=True)
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DistrictSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = District.objects.filter(is_active=True)
        region = self.request.query_params.get("region")
        return qs.filter(region_id=region) if region else qs


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "shop": ShopSerializer(user.shop, context={"request": request}).data,
        }, status=201)


class MeView(APIView):
    """Joriy do'kon egasi + do'koni ma'lumotlari."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shop = getattr(request.user, "shop", None)
        return Response({
            "phone": request.user.phone,
            "full_name": request.user.full_name,
            "role": request.user.role,
            "shop": ShopSerializer(shop, context={"request": request}).data if shop else None,
        })
