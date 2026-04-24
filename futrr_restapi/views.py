from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from users.models import EmailQueue, SupportTicket, Subscription, FutrrUser


# ── Sidebar nav helper ──────────────────────────
ADMIN_NAV = [
    ("Mail Queue", "/api/su/mail-queue/"),
    ("Tickets", "/api/su/tickets/"),
    ("Subscriptions", "/api/su/upgrade/"),
    ("Django Admin", "/admin/"),
]


# ── Mail Queue ───────────────────────────────────

@staff_member_required
def mail_queue_view(request):
    qs = EmailQueue.objects.all().order_by("-created_at")

    filter_status = request.GET.get("status", "")
    filter_priority = request.GET.get("priority", "")
    filter_type = request.GET.get("type", "")

    if filter_status:
        qs = qs.filter(status=filter_status)
    if filter_priority:
        qs = qs.filter(priority=filter_priority)
    if filter_type:
        qs = qs.filter(email_type=filter_type)

    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get("page", 1))

    counts = {
        "total": EmailQueue.objects.count(),
        "pending": EmailQueue.objects.filter(status="pending").count(),
        "sent": EmailQueue.objects.filter(status="sent").count(),
        "failed": EmailQueue.objects.filter(status="failed").count(),
    }

    return render(request, "mail_queue.html", {
        "page": page,
        "counts": counts,
        "filter_status": filter_status,
        "filter_priority": filter_priority,
        "filter_type": filter_type,
        "user": request.user,
        "nav": ADMIN_NAV,
        "active_page": "Mail Queue",
    })


# ── Support Tickets ──────────────────────────────

@staff_member_required
def tickets_view(request):
    qs = SupportTicket.objects.select_related("user").all()

    filter_status = request.GET.get("status", "")
    filter_category = request.GET.get("category", "")

    if filter_status:
        qs = qs.filter(status=filter_status)
    if filter_category:
        qs = qs.filter(category=filter_category)

    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get("page", 1))

    counts = {
        "total": SupportTicket.objects.count(),
        "open": SupportTicket.objects.filter(status="open").count(),
        "resolved": SupportTicket.objects.filter(status="resolved").count(),
        "closed": SupportTicket.objects.filter(status="closed").count(),
    }

    return render(request, "tickets.html", {
        "page": page,
        "counts": counts,
        "filter_status": filter_status,
        "filter_category": filter_category,
        "user": request.user,
        "nav": ADMIN_NAV,
        "active_page": "Tickets",
    })


@staff_member_required
@require_POST
def ticket_update_status(request, ticket_id):
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)
    except SupportTicket.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    new_status = request.POST.get("status", "")
    if new_status in dict(SupportTicket.Status.choices):
        ticket.status = new_status
        ticket.save(update_fields=["status", "updated_at"])

    return redirect("/api/su/tickets/")


# ── Subscriptions (manage user plans) ────────────

def _Q(*args, **kwargs):
    from django.db.models import Q
    return Q(*args, **kwargs)


@staff_member_required
def upgrade_view(request):
    search = request.GET.get("q", "").strip()
    selected_user = None
    sub = None

    if search:
        selected_user = FutrrUser.objects.filter(
            _Q(email__iexact=search) | _Q(username__iexact=search)
        ).first()
        if selected_user:
            sub, _ = Subscription.objects.get_or_create(user=selected_user)

    return render(request, "upgrade.html", {
        "search": search,
        "selected_user": selected_user,
        "sub": sub,
        "user": request.user,
        "nav": ADMIN_NAV,
        "active_page": "Subscriptions",
    })


@staff_member_required
@require_POST
def upgrade_save(request):
    user_id = request.POST.get("user_id")
    if not user_id:
        return redirect("/api/su/upgrade/")

    try:
        target = FutrrUser.objects.get(id=user_id)
    except FutrrUser.DoesNotExist:
        return redirect("/api/su/upgrade/")

    sub, _ = Subscription.objects.get_or_create(user=target)

    # Integer fields
    int_fields = [
        "max_capsules_per_week", "max_events_per_week",
        "max_event_participants", "max_recipients_per_capsule",
        "max_media_per_capsule", "max_storage_mb", "max_favorites",
    ]
    for field in int_fields:
        val = request.POST.get(field)
        if val and val.isdigit():
            setattr(sub, field, int(val))

    # Float fields
    float_fields = ["atlas_radius_miles", "atlas_radius_growth"]
    for field in float_fields:
        val = request.POST.get(field)
        if val:
            try:
                setattr(sub, field, float(val))
            except ValueError:
                pass

    # Tier
    tier = request.POST.get("tier", sub.tier)
    if tier in dict(Subscription.TIER_CHOICES):
        sub.tier = tier

    # Expiry
    from django.utils.dateparse import parse_datetime
    expires_raw = request.POST.get("expires_at", "").strip()
    if expires_raw:
        parsed = parse_datetime(expires_raw)
        if parsed:
            from django.utils import timezone as tz
            sub.expires_at = parsed if parsed.tzinfo else tz.make_aware(parsed)
    elif "clear_expiry" in request.POST:
        sub.expires_at = None

    # Notes
    notes = request.POST.get("notes", "").strip()
    sub.notes = notes

    # Auto-set tier to free+ if any value differs from free defaults
    FREE_DEFAULTS = {
        "max_capsules_per_week": 5, "max_events_per_week": 1,
        "max_event_participants": 200, "max_recipients_per_capsule": 5,
        "max_media_per_capsule": 10, "max_storage_mb": 100,
        "max_favorites": 25, "atlas_radius_miles": 1.0,
        "atlas_radius_growth": 0.5,
    }
    if sub.tier == "free":
        for k, default_val in FREE_DEFAULTS.items():
            if getattr(sub, k) != default_val:
                sub.tier = "free+"
                break

    sub.save()
    return redirect(f"/api/su/upgrade/?q={target.email}")
