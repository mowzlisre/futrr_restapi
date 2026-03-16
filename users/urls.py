from django.urls import path
from .api import (
    SignUpView, LoginView, LogoutView, OAuthView,
    PasswordResetView, TwoFactorView, ChangePasswordView,
    UserProfileView, DeleteAccountView,
    UserSearchView, PublicUserProfileView, FollowView,
)

urlpatterns = [
    # Authentication
    path('signup/', SignUpView.signup, name='signup'),
    path('login/', LoginView.login, name='login'),
    path('logout/', LogoutView.logout, name='logout'),
    path('delete-account/', DeleteAccountView.delete_account, name='delete-account'),

    # OAuth
    path('oa/google/', OAuthView.google_oauth, name='google-oauth'),

    # Password management
    path('password/forget/', PasswordResetView.forget_password, name='forget-password'),
    path('password/reset/', PasswordResetView.reset_password, name='reset-password'),
    path('password/change/', ChangePasswordView.change_password, name='change-password'),

    # 2FA device management
    path('2fa/device/add/', TwoFactorView.add_device, name='add-2fa-device'),
    path('2fa/device/remove/', TwoFactorView.remove_device, name='remove-2fa-device'),
    path('2fa/device/verify/', TwoFactorView.verify_device, name='verify-2fa-device'),
    path('2fa/devices/', TwoFactorView.list_devices, name='list-2fa-devices'),

    # User profile
    path('me/', UserProfileView.get_me, name='user-me-get'),
    path('me/update/', UserProfileView.update_me, name='user-me-update'),
    path('me/followers/', FollowView.followers, name='my-followers'),
    path('me/following/', FollowView.following, name='my-following'),

    # Social
    path('search/', UserSearchView.search, name='user-search'),
    path('<uuid:user_id>/', PublicUserProfileView.get_user, name='user-profile'),
    path('<uuid:user_id>/follow/', FollowView.follow, name='user-follow'),
    path('<uuid:user_id>/unfollow/', FollowView.unfollow, name='user-unfollow'),
]