from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from users.models import EmailQueue, SupportTicket, UserQuota, FutrrUser


# ── Sidebar nav helper ──────────────────────────
ADMIN_NAV = [
    ("Mail Queue", "/api/su/mail-queue/"),
    ("Tickets", "/api/su/tickets/"),
    ("Upgrade", "/api/su/upgrade/"),
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


# ── Upgrade (manage user quotas) ─────────────────

@staff_member_required
def upgrade_view(request):
    search = request.GET.get("q", "").strip()
    selected_user = None
    quota = None

    if search:
        selected_user = FutrrUser.objects.filter(
            models_Q(email__iexact=search) | models_Q(username__iexact=search)
        ).first()
        if selected_user:
            quota, _ = UserQuota.objects.get_or_create(user=selected_user)

    return render(request, "upgrade.html", {
        "search": search,
        "selected_user": selected_user,
        "quota": quota,
        "user": request.user,
        "nav": ADMIN_NAV,
        "active_page": "Upgrade",
    })


def models_Q(*args, **kwargs):
    from django.db.models import Q
    return Q(*args, **kwargs)


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

    quota, _ = UserQuota.objects.get_or_create(user=target)

    tier = request.POST.get("tier", quota.tier)
    max_event = request.POST.get("max_event_participants")
    max_recip = request.POST.get("max_capsule_recipients")

    if tier:
        quota.tier = tier
    if max_event and max_event.isdigit():
        quota.max_event_participants = int(max_event)
    if max_recip and max_recip.isdigit():
        quota.max_capsule_recipients = int(max_recip)

    quota.save()
    return redirect(f"/api/su/upgrade/?q={target.email}")
