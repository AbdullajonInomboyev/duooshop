"""
Admin bosh sahifasidagi statistika.
Jazzmin index shablonига 'dashboard_stats' konteksti orqali uzatiladi.
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count


def get_dashboard_stats():
    from orders.models import Order, Payment
    from accounts.models import Shop

    today = timezone.now().date()
    month_start = today.replace(day=1)

    orders_today = Order.objects.filter(created_at__date=today)
    orders_month = Order.objects.filter(created_at__date__gte=month_start)

    # Umumiy savdo (bekor qilinmaganlar)
    sales_today = orders_today.exclude(status="cancelled").aggregate(
        s=Sum("total"))["s"] or 0
    sales_month = orders_month.exclude(status="cancelled").aggregate(
        s=Sum("total"))["s"] or 0

    # Qarzdorlik (jami do'konlar qarzi)
    total_debt = Shop.objects.aggregate(d=Sum("debt_balance"))["d"] or 0

    return {
        "orders_today": orders_today.count(),
        "sales_today": sales_today,
        "sales_month": sales_month,
        "new_orders": Order.objects.filter(status="new").count(),
        "shops_total": Shop.objects.count(),
        "shops_new": Shop.objects.filter(is_new=True).count(),
        "total_debt": total_debt,
        # Oxirgi 5 buyurtma
        "recent_orders": Order.objects.select_related("shop")
            .order_by("-created_at")[:5],
    }
