from django.urls import path
from .api import (
    SignUpView, LoginView, LogoutView, OAuthView,
    PasswordResetView, TwoFactorView, ChangePasswordView
)

urlpatterns = [
    # Authentication endpoints
    path('signup/', SignUpView.signup, name='signup'),
    path('login/', LoginView.login, name='login'),
    path('logout/', LogoutView.logout, name='logout'),
    
    # OAuth endpoints
    path('oa/google/', OAuthView.google_oauth, name='google-oauth'),
    path('oa/github/', OAuthView.github_oauth, name='github-oauth'),
    
    # Password management
    path('password/forget/', PasswordResetView.forget_password, name='forget-password'),
    path('password/reset/', PasswordResetView.reset_password, name='reset-password'),
    path('password/change/', ChangePasswordView.change_password, name='change-password'),
    
    # 2FA device management
    path('2fa/device/add/', TwoFactorView.add_device, name='add-2fa-device'),
    path('2fa/device/remove/', TwoFactorView.remove_device, name='remove-2fa-device'),
    path('2fa/device/verify/', TwoFactorView.verify_device, name='verify-2fa-device'),
    path('2fa/devices/', TwoFactorView.list_devices, name='list-2fa-devices'),
]