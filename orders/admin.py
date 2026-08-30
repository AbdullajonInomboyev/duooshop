from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html
from django.db.models import Sum
from .models import Cart, CartItem, Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "unit_price", "quantity", "unit", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "shop", "status_badge", "payment_type",
                    "total_display", "courier", "created_at", "waybill_link")

    @admin.display(description="Yuk xati")
    def waybill_link(self, obj):
        return format_html(
            '<a href="/admin/waybill/order/{}/" target="_blank" '
            'style="color:#009D4D;font-weight:600">📄 Yuk xati</a>', obj.id)
    list_filter = ("status", "payment_type", "created_at", "shop__region")
    search_fields = ("receipt_number", "shop__name", "shop__owner__phone")
    readonly_fields = ("receipt_number", "items_total", "total",
                       "created_at", "confirmed_at", "delivered_at", "paid_at")
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    list_per_page = 25

    # ---- Rangli holat belgisi ----
    @admin.display(description="Holat")
    def status_badge(self, obj):
        colors = {
            "new": "#f9a825", "confirmed": "#1976d2", "packed": "#7b1fa2",
            "on_the_way": "#0288d1", "delivered": "#2e7d32",
            "paid": "#2e7d32", "cancelled": "#c62828",
        }
        c = colors.get(obj.status, "#666")
        return format_html(
            '<span style="background:{}20;color:{};padding:3px 10px;'
            'border-radius:12px;font-weight:600;white-space:nowrap">{}</span>',
            c, c, obj.get_status_display())

    @admin.display(description="Jami", ordering="total")
    def total_display(self, obj):
        return format_html("<b>{:,.0f}</b> so'm".format(obj.total).replace(",", " "))

    # ---- Tugmali harakatlar ----
    actions = ["mark_confirmed", "mark_packed", "mark_on_the_way",
               "mark_delivered", "mark_paid", "mark_cancelled"]

    @admin.action(description="✅ Tasdiqlash")
    def mark_confirmed(self, request, queryset):
        n = queryset.update(status="confirmed", confirmed_at=timezone.now())
        self.message_user(request, f"{n} ta buyurtma tasdiqlandi.", messages.SUCCESS)

    @admin.action(description="📦 Yig'ildi deb belgilash")
    def mark_packed(self, request, queryset):
        n = queryset.update(status="packed")
        self.message_user(request, f"{n} ta buyurtma yig'ildi.", messages.SUCCESS)

    @admin.action(description="🚚 Yo'lda deb belgilash")
    def mark_on_the_way(self, request, queryset):
        n = queryset.update(status="on_the_way")
        self.message_user(request, f"{n} ta buyurtma yo'lga chiqdi.", messages.SUCCESS)

    @admin.action(description="✔️ Yetkazildi deb belgilash")
    def mark_delivered(self, request, queryset):
        n = queryset.update(status="delivered", delivered_at=timezone.now())
        self.message_user(request, f"{n} ta buyurtma yetkazildi.", messages.SUCCESS)

    @admin.action(description="💰 To'landi deb belgilash (qarzdan chiqarish)")
    def mark_paid(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status != "paid":
                # Nasiya bo'lgan bo'lsa, do'kon qarzini kamaytiramiz
                if order.payment_type == "credit":
                    shop = order.shop
                    shop.debt_balance = max(0, shop.debt_balance - order.total)
                    shop.save(update_fields=["debt_balance"])
                    Payment.objects.create(
                        shop=shop, order=order, amount=order.total,
                        note="Buyurtma to'landi", received_by=request.user)
                order.status = "paid"
                order.paid_at = timezone.now()
                order.save(update_fields=["status", "paid_at"])
                count += 1
        self.message_user(request, f"{count} ta buyurtma to'landi.", messages.SUCCESS)

    @admin.action(description="❌ Bekor qilish")
    def mark_cancelled(self, request, queryset):
        n = queryset.update(status="cancelled")
        self.message_user(request, f"{n} ta buyurtma bekor qilindi.", messages.WARNING)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("shop", "amount_display", "order", "received_by", "created_at")
    list_filter = ("created_at", "shop__region")
    search_fields = ("shop__name", "order__receipt_number")
    date_hierarchy = "created_at"

    @admin.display(description="Summa", ordering="amount")
    def amount_display(self, obj):
        return format_html("<b>{:,.0f}</b> so'm".format(obj.amount).replace(",", " "))


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("shop", "updated_at")