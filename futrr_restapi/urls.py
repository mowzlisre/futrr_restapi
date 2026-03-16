from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.api import DeleteAccountView

urlpatterns = [
    # Token refresh (background auto-refresh used by mobile)
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('admin/', admin.site.urls),

    # All user-facing auth + profile endpoints under /api/users/
    path('api/users/', include('users.urls')),

    # Delete account kept at /api/auth/delete-account/ per mobile spec
    path('api/auth/delete-account/', DeleteAccountView.delete_account, name='delete-account-auth'),

    # Capsules, events, discover, notifications
    path('api/', include('app.urls')),
]
