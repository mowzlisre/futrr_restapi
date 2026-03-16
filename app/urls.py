from django.urls import path
from .api import (
    CapsuleListCreateView,
    CapsuleDetailView,
    CapsuleRecipientView,
    CapsuleJoinView,
    CapsuleUnlockView,
    CapsuleContentView,
    CapsuleMapView,
    CapsuleFavoriteView,
    CapsuleFavoritesListView,
    EventListCreateView,
    EventDetailView,
    EventJoinView,
    EventCapsulesView,
    DiscoverView,
    DiscoverSearchView,
    FriendsFeedView,
    GlobalFeedView,
    NotificationListView,
    NotificationReadView,
)

urlpatterns = [
    # Capsules
    path("capsules/", CapsuleListCreateView.as_view(), name="capsule-list-create"),
    path("capsules/map/", CapsuleMapView.as_view(), name="capsule-map"),
    path("capsules/favorites/", CapsuleFavoritesListView.as_view(), name="capsule-favorites-list"),
    path("capsules/join/<uuid:share_token>/", CapsuleJoinView.as_view(), name="capsule-join"),
    path("capsules/<uuid:capsule_id>/", CapsuleDetailView.as_view(), name="capsule-detail"),
    path("capsules/<uuid:capsule_id>/recipients/", CapsuleRecipientView.as_view(), name="capsule-add-recipient"),
    path("capsules/<uuid:capsule_id>/unlock/", CapsuleUnlockView.as_view(), name="capsule-unlock"),
    path("capsules/<uuid:capsule_id>/contents/", CapsuleContentView.as_view(), name="capsule-content"),
    path("capsules/<uuid:capsule_id>/favorite/", CapsuleFavoriteView.as_view(), name="capsule-favorite"),

    # Discover feed
    path("discover/", DiscoverView.as_view(), name="discover"),
    path("discover/search/", DiscoverSearchView.as_view(), name="discover-search"),
    path("discover/friends/", FriendsFeedView.as_view(), name="discover-friends"),
    path("discover/global/", GlobalFeedView.as_view(), name="discover-global"),

    # Events
    path("events/", EventListCreateView.as_view(), name="event-create"),
    path("events/join/<uuid:invite_token>/", EventJoinView.as_view(), name="event-join"),
    path("events/<uuid:event_id>/", EventDetailView.as_view(), name="event-detail"),
    path("events/<uuid:event_id>/capsules/", EventCapsulesView.as_view(), name="event-capsules"),

    # Notifications
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/<uuid:notif_id>/read/", NotificationReadView.as_view(), name="notification-read"),
]
