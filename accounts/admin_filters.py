"""
Zanjirli (bog'liq) filtrlar admin panel uchun.
Tuman filtri faqat tanlangan viloyatning tumanlarini ko'rsatadi.
"""
from django.contrib import admin
from .models import District


class RegionFilter(admin.SimpleListFilter):
    title = "Viloyat"
    parameter_name = "region"

    def lookups(self, request, model_admin):
        from .models import Region
        return [(r.id, r.name) for r in Region.objects.filter(is_active=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(region_id=self.value())
        return queryset


class ChainedDistrictFilter(admin.SimpleListFilter):
    """Faqat tanlangan viloyatning tumanlarini ko'rsatadi (zanjirli)."""
    title = "Tuman"
    parameter_name = "district"

    def lookups(self, request, model_admin):
        region_id = request.GET.get("region")
        qs = District.objects.filter(is_active=True)
        if region_id:
            qs = qs.filter(region_id=region_id)
        else:
            # Viloyat tanlanmagan bo'lsa, tuman ro'yxatini bermaslik
            # (juda uzun bo'lmasligi uchun)
            return []
        return [(d.id, d.name) for d in qs]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(district_id=self.value())
        return queryset