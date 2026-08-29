from rest_framework import serializers
from .models import Banner, PromoScreen


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "title", "image", "link_type", "link_value"]


class PromoScreenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoScreen
        fields = ["id", "title", "body", "image", "placement",
                  "skip_after_seconds"]
