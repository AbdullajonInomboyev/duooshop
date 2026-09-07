"""
Yuk xati (накладная) — chop etiladigan hujjatlar.
1. Bitta buyurtma uchun yuk xati.
2. Sana bo'yicha jamlangan yuk xati (umumiy miqdor + do'kon taqsimoti).
Faqat admin (staff) foydalanuvchilar uchun.
"""
from collections import defaultdict, OrderedDict
from datetime import datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Order, OrderItem


@staff_member_required
def waybill_single(request, order_id):
    """Bitta buyurtma uchun yuk xati."""
    order = get_object_or_404(Order.objects.select_related("shop"), pk=order_id)
    items = order.items.select_related("product", "product__category").all()

    rows = []
    for i, it in enumerate(items, 1):
        category = ""
        if it.product and it.product.category:
            category = it.product.category.name
        rows.append({
            "n": i,
            "category": category,
            "name": it.product_name,
            "price": it.unit_price,
            "qty": it.quantity,
            "total": it.line_total,
        })

    context = {
        "order": order,
        "shop": order.shop,
        "rows": rows,
        "grand_total": order.total,
        "date": order.created_at,
    }
    return render(request, "admin/waybill_single.html", context)


@staff_member_required
def waybill_grouped(request):
    """
    Sana bo'yicha jamlangan yuk xati.
    ?date=YYYY-MM-DD (bo'lmasa bugun).
    Qism 1: umumiy miqdor (mahsulot bo'yicha jami).
    Qism 2: do'kon taqsimoti (qaysi do'kon nima oldi).
    """
    date_str = request.GET.get("date")
    if date_str:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            day = timezone.now().date()
    else:
        day = timezone.now().date()

    orders = (Order.objects.filter(created_at__date=day)
              .exclude(status="cancelled")
              .select_related("shop"))

    # Qism 1: umumiy miqdor (mahsulot nomi bo'yicha jamlash)
    totals = defaultdict(lambda: {"qty": 0, "category": "", "unit": ""})
    # Qism 2: do'kon taqsimoti
    by_shop = OrderedDict()

    for order in orders:
        shop_name = order.shop.name
        if shop_name not in by_shop:
            by_shop[shop_name] = []
        for it in order.items.select_related("product", "product__category"):
            cat = (it.product.category.name
                   if it.product and it.product.category else "")
            key = it.product_name
            totals[key]["qty"] += it.quantity
            totals[key]["category"] = cat
            totals[key]["unit"] = it.unit
            by_shop[shop_name].append({
                "category": cat,
                "name": it.product_name,
                "qty": it.quantity,
                "unit": it.unit,
                "total": it.line_total,
            })

    # Umumiy miqdorni tartiblash (kategoriya, keyin nom bo'yicha)
    summary = []
    for i, (name, data) in enumerate(
            sorted(totals.items(), key=lambda x: (x[1]["category"], x[0])), 1):
        summary.append({
            "n": i,
            "category": data["category"],
            "name": name,
            "qty": data["qty"],
            "unit": data["unit"],
        })

    context = {
        "day": day,
        "summary": summary,
        "by_shop": by_shop,
        "order_count": orders.count(),
        "shop_count": len(by_shop),
    }
    return render(request, "admin/waybill_grouped.html", context)


@staff_member_required
def waybill_multiple(request):
    """
    Bir nechta buyurtma uchun yuk xati — bitta sahifada, har biri
    '- - - -' bilan ajratilgan. Chop etish/PDF uchun.
    ?ids=1,2,3 (buyurtma ID'lari).
    """
    ids_str = request.GET.get("ids", "")
    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    orders = (Order.objects.filter(pk__in=ids)
              .select_related("shop").order_by("shop__name"))

    waybills = []
    for order in orders:
        items = order.items.select_related("product", "product__category").all()
        rows = []
        for i, it in enumerate(items, 1):
            category = ""
            if it.product and it.product.category:
                category = it.product.category.name
            rows.append({
                "n": i, "category": category, "name": it.product_name,
                "price": it.unit_price, "qty": it.quantity, "total": it.line_total,
            })
        waybills.append({
            "order": order, "shop": order.shop, "rows": rows,
            "grand_total": order.total, "date": order.created_at,
        })

    return render(request, "admin/waybill_multiple.html", {"waybills": waybills})