from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Region, District, Shop

User = get_user_model()


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "name"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name", "region"]


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ["id", "name", "image", "region", "district",
                  "latitude", "longitude", "address_text",
                  "debt_balance", "credit_limit", "is_active", "is_approved"]
        read_only_fields = ["debt_balance", "credit_limit", "is_active",
                            "is_approved"]


class RegisterSerializer(serializers.Serializer):
    """
    Do'kon egasi ro'yxatdan o'tishi. Tasdiqlash yo'q -> darhol faol.
    Viloyat/tuman NOM (matn) sifatida keladi (ilova offline ro'yxatdan
    oladi); bazada bo'lmasa avtomatik yaratiladi. Rasm ixtiyoriy.
    """
    phone = serializers.CharField(max_length=20)
    full_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=4)
    shop_name = serializers.CharField(max_length=200)
    region_name = serializers.CharField(max_length=100)
    district_name = serializers.CharField(max_length=100)
    image = serializers.ImageField(required=False, allow_null=True)
    # FloatField — GPS qancha xona bersa ham qabul qiladi (cheklov yo'q),
    # create() da 6 xonaga yaxlitlanadi. Shunday xato bermaydi.
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    address_text = serializers.CharField(required=False, allow_blank=True)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqam ro'yxatdan o'tgan.")
        return value

    def create(self, validated):
        # Viloyat/tumanni nom bo'yicha topamiz yoki yaratamiz
        region, _ = Region.objects.get_or_create(
            name=validated["region_name"].strip())
        district, _ = District.objects.get_or_create(
            region=region, name=validated["district_name"].strip())

        user = User.objects.create_user(
            username=validated["phone"],
            phone=validated["phone"],
            full_name=validated["full_name"],
            password=validated["password"],
            role=User.Role.SHOP,
            region=region,
        )
        # Koordinatani 6 xonaga yaxlitlaymiz (GPS ko'p xona bersa ham)
        lat = validated.get("latitude")
        lng = validated.get("longitude")
        lat = round(lat, 6) if lat is not None else None
        lng = round(lng, 6) if lng is not None else None

        Shop.objects.create(
            owner=user,
            name=validated["shop_name"],
            image=validated.get("image"),
            region=region,
            district=district,
            latitude=lat,
            longitude=lng,
            address_text=validated.get("address_text", ""),
        )
        return user