from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.api import DeleteAccountView
from futrr_restapi.views import (
    mail_queue_view,
    tickets_view,
    ticket_update_status,
    upgrade_view,
    upgrade_save,
)

urlpatterns = [
    path('api/health/', lambda request: JsonResponse({"status": "ok"}), name='health'),

    # Token refresh (background auto-refresh used by mobile)
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('admin/', admin.site.urls),

    # All user-facing auth + profile endpoints under /api/users/
    path('api/users/', include('users.urls')),

    # Delete account kept at /api/auth/delete-account/ per mobile spec
    path('api/auth/delete-account/', DeleteAccountView.delete_account, name='delete-account-auth'),

    # Capsules, events, discover, notifications
    path('api/', include('app.urls')),

    # ── Superuser admin panels (/api/su/) ──
    path('api/su/mail-queue/', mail_queue_view, name='mail-queue'),
    path('api/su/tickets/', tickets_view, name='tickets'),
    path('api/su/tickets/<uuid:ticket_id>/status/', ticket_update_status, name='ticket-update-status'),
    path('api/su/upgrade/', upgrade_view, name='upgrade'),
    path('api/su/upgrade/save/', upgrade_save, name='upgrade-save'),
]
