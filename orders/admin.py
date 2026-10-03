from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from rangefilter.filters import DateRangeFilter
from .models import Cart, CartItem, Order, OrderItem, Payment


# ============================================================
# BUYURTMA QATORI (INLINE)
# ============================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product_name", "unit_price", "quantity", "unit", "line_total")
    readonly_fields = ("product_name", "unit_price", "unit", "line_total")
    can_delete = True

    def has_add_permission(self, request, obj=None):
        return False  # Tasdiqlangan buyurtmaga to'g'ridan-to'g'ri yangi mahsulot qo'shilmaydi


# ============================================================
# BUYURTMA ADMINI
# ============================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_number",
        "shop",
        "status_badge",
        "payment_type",
        "total_display",
        "courier",
        "created_at",
        "waybill_actions",
    )
    list_filter = (
        ("created_at", DateRangeFilter),
        "status",
        "payment_type",
        "shop__region",
        "shop",
    )
    search_fields = (
        "receipt_number",
        "shop__name",
        "shop__owner__phone",
        "user__phone",
        "user__username",
    )
    readonly_fields = (
        "receipt_number",
        "items_total",
        "total",
        "created_at",
        "updated_at",
        "confirmed_at",
        "delivered_at",
        "paid_at",
    )
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    list_per_page = 25

    def save_related(self, request, form, formsets, change):
        """Admin mahsulot miqdorini o'zgartirganda summalarni avtomatik qayta hisoblash."""
        super().save_related(request, form, formsets, change)
        order = form.instance
        
        # Har bir qator summasini yangilaymiz
        for item in order.items.all():
            new_line_total = item.unit_price * item.quantity
            if item.line_total != new_line_total:
                item.line_total = new_line_total
                item.save(update_fields=["line_total"])

        # Buyurtma umumiy summasini qayta hisoblash (modeldagi metod yoki to'g'ridan-to'g'ri)
        if hasattr(order, "recalculate_totals"):
            order.recalculate_totals(save=True)
        else:
            items_sum = order.items.aggregate(s=Sum("line_total"))["s"] or 0
            order.items_total = items_sum
            order.total = items_sum + getattr(order, "delivery_fee", 0) - getattr(order, "discount_amount", 0)
            order.save(update_fields=["items_total", "total"])

    # ---- Rangli holat nishoni ----
    @admin.display(description="Holat")
    def status_badge(self, obj):
        colors = {
            "new": "#f9a825",
            "confirmed": "#1976d2",
            "packed": "#7b1fa2",
            "on_the_way": "#0288d1",
            "delivered": "#2e7d32",
            "paid": "#2e7d32",
            "cancelled": "#c62828",
        }
        c = colors.get(obj.status, "#666")
        return format_html(
            '<span style="background:{}20;color:{};padding:4px 10px;'
            'border-radius:12px;font-weight:600;white-space:nowrap">{}</span>',
            c, c, obj.get_status_display()
        )

    # ---- Formatlangan summa ----
    @admin.display(description="Jami summa", ordering="total")
    def total_display(self, obj):
        return format_html("<b>{:,.0f}</b> so'm".format(obj.total).replace(",", " "))

    # ---- Yuk xati (HTML va Excel) tugmalari ----
    @admin.display(description="Hujjatlar")
    def waybill_actions(self, obj):
        try:
            html_url = reverse("waybill-single", args=[obj.id])
            excel_url = f"{html_url}?export=excel"
        except Exception:
            html_url = f"/admin/waybill/order/{obj.id}/"
            excel_url = f"{html_url}?export=excel"

        return format_html(
            '<div style="display:flex;gap:5px;">'
            '<a href="{}" target="_blank" style="background:#e8f5e9;color:#2e7d32;padding:3px 7px;border-radius:4px;font-weight:600;text-decoration:none;font-size:12px;">'
            '📄 HTML</a>'
            '<a href="{}" style="background:#28a745;color:white;padding:3px 7px;border-radius:4px;font-weight:600;text-decoration:none;font-size:12px;">'
            '📥 Excel</a>'
            '</div>',
            html_url,
            excel_url,
        )

    # ---- Ommaviy harakatlar (Admin Actions) ----
    actions = [
        "print_waybills",
        "print_by_brand",
        "mark_confirmed",
        "mark_packed",
        "mark_on_the_way",
        "mark_delivered",
        "mark_paid",
        "mark_cancelled",
    ]

    @admin.action(description="🏭 Tanlanganlarni brend bo'yicha yuk xati")
    def print_by_brand(self, request, queryset):
        from django.shortcuts import redirect
        ids = ",".join(str(o.id) for o in queryset)
        return redirect(f"/admin/waybill/selected-by-brand/?ids={ids}")

    @admin.action(description="📄 Tanlanganlarning yuk xati (bitta varaqda)")
    def print_waybills(self, request, queryset):
        from django.shortcuts import redirect
        ids = ",".join(str(o.id) for o in queryset)
        return redirect(f"/admin/waybill/multiple/?ids={ids}")

    @admin.action(description="Tasdiqlash")
    def mark_confirmed(self, request, queryset):
        n = queryset.update(status="confirmed", confirmed_at=timezone.now())
        self.message_user(request, f"{n} ta buyurtma tasdiqlandi.", messages.SUCCESS)

    @admin.action(description="Yig'ildi deb belgilash")
    def mark_packed(self, request, queryset):
        n = queryset.update(status="packed")
        self.message_user(request, f"{n} ta buyurtma yig'ildi.", messages.SUCCESS)

    @admin.action(description="Yo'lga chiqdi deb belgilash")
    def mark_on_the_way(self, request, queryset):
        n = queryset.update(status="on_the_way")
        self.message_user(request, f"{n} ta buyurtma yo'lga chiqdi.", messages.SUCCESS)

    @admin.action(description="Yetkazildi deb belgilash")
    def mark_delivered(self, request, queryset):
        n = queryset.update(status="delivered", delivered_at=timezone.now())
        self.message_user(request, f"{n} ta buyurtma yetkazildi.", messages.SUCCESS)

    @admin.action(description="To'landi deb belgilash (qarzdan yechish)")
    def mark_paid(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status != "paid":
                # Nasiya bo'lsa do'kon qarzini kamaytiramiz va Payment yaratamiz
                if order.payment_type == "credit" and order.shop:
                    shop = order.shop
                    if hasattr(shop, "debt_balance"):
                        shop.debt_balance = max(0, shop.debt_balance - order.total)
                        shop.save(update_fields=["debt_balance"])
                    
                    Payment.objects.create(
                        shop=shop,
                        order=order,
                        amount=order.total,
                        note="Buyurtma to'landi (admin)",
                        received_by=request.user,
                    )

                order.status = "paid"
                order.paid_at = timezone.now()
                order.save(update_fields=["status", "paid_at"])
                count += 1

        self.message_user(request, f"{count} ta buyurtma to'landi deb belgilandi.", messages.SUCCESS)

    @admin.action(description="Bekor qilish")
    def mark_cancelled(self, request, queryset):
        n = queryset.update(status="cancelled")
        self.message_user(request, f"{n} ta buyurtma bekor qilindi.", messages.WARNING)


# ============================================================
# TO'LOVLAR (PAYMENT) ADMINI
# ============================================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("shop", "amount_display", "order", "received_by", "created_at")
    list_filter = ("created_at", "shop__region")
    search_fields = ("shop__name", "order__receipt_number", "note")
    date_hierarchy = "created_at"

    @admin.display(description="Summa", ordering="amount")
    def amount_display(self, obj):
        return format_html("<b>{:,.0f}</b> so'm".format(obj.amount).replace(",", " "))


# ============================================================
# SAVATCHA (CART) ADMINI
# ============================================================
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("product", "quantity", "line_total")
    readonly_fields = ("line_total",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("shop", "total_display", "updated_at")
    inlines = [CartItemInline]

    @admin.display(description="Savat summasi")
    def total_display(self, obj):
        return format_html("<b>{:,.0f}</b> so'm".format(obj.total).replace(",", " "))