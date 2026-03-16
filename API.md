# Futrr REST API Documentation

## Base URL
```
https://api.futrr.app
```

## Overview
The Futrr REST API powers the futrr mobile app (iOS & Android). It covers authentication, user profile management, time-locked capsule creation with encrypted media, group events, a public discovery feed, an Atlas map view, favorites, and in-app notifications.

## Authentication
JWT (JSON Web Tokens). Include the access token in every protected request:
```
Authorization: Bearer <access_token>
```
Access tokens expire after 5 minutes. Use `/api/token/refresh/` to silently renew them in the background.

---

## Endpoint Index

| # | Method | Endpoint | Screen / Feature | Auth |
|---|--------|----------|-----------------|------|
| 1 | POST | `/api/token/refresh/` | Background token refresh | No |
| 2 | POST | `/api/users/signup/` | Login screen — sign up | No |
| 3 | POST | `/api/users/login/` | Login screen — sign in | No |
| 4 | POST | `/api/users/logout/` | Profile → Sign out | Yes |
| 5 | POST | `/api/users/oa/google/` | Login → Google sign-in | No |
| 6 | POST | `/api/users/password/forget/` | Forgot password | No |
| 7 | POST | `/api/users/password/reset/` | Forgot password (confirm) | No |
| 8 | POST | `/api/users/password/change/` | Settings → Security | Yes |
| 9 | POST | `/api/users/2fa/device/add/` | Settings → Security | Yes |
| 10 | POST | `/api/users/2fa/device/verify/` | Settings → Security | Yes |
| 11 | POST | `/api/users/2fa/device/remove/` | Settings → Security | Yes |
| 12 | GET | `/api/users/2fa/devices/` | Settings → Security | Yes |
| 13 | GET | `/api/users/me/` | Profile screen, app init | Yes |
| 14 | PATCH | `/api/users/me/update/` | Profile → Edit | Yes |
| 15 | DELETE | `/api/auth/delete-account/` | Settings → Delete account | Yes |
| 16 | GET | `/api/capsules/` | Vault (capsule list) | Yes |
| 17 | POST | `/api/capsules/` | Create Capsule modal | Yes |
| 18 | GET | `/api/capsules/:id/` | Capsule detail screen | Yes |
| 19 | DELETE | `/api/capsules/:id/` | Capsule detail → delete | Yes |
| 20 | POST | `/api/capsules/:id/contents/` | Create Capsule → add text / photo / voice | Yes |
| 21 | POST | `/api/capsules/:id/recipients/` | Create Capsule → Send To | Yes |
| 22 | POST | `/api/capsules/:id/favorite/` | Capsule detail → heart | Yes |
| 23 | GET | `/api/capsules/join/:share_token/` | Deep link / QR code join | Yes |
| 24 | GET | `/api/capsules/map/` | Atlas screen (map pins) | Yes |
| 25 | GET | `/api/discover/` | Discover feed | Yes |
| 26 | POST | `/api/events/` | Create collective capsule | Yes |
| 27 | GET | `/api/events/:id/` | Event detail | Yes |
| 28 | POST | `/api/events/join/:invite_token/` | Join event via invite | Yes |
| 29 | GET | `/api/events/:id/capsules/` | Event → group capsule list | Yes |
| 30 | GET | `/api/notifications/` | Notifications screen | Yes |
| 31 | PATCH | `/api/notifications/:id/read/` | Mark notification read | Yes |

---

## Token Management

### Refresh Access Token
- **URL**: `POST /api/token/refresh/`
- **Auth**: None
- **Body**:
  ```json
  { "refresh": "string" }
  ```
- **Response** (200):
  ```json
  { "access": "string" }
  ```

---

## User Authentication

### Sign Up
- **URL**: `POST /api/users/signup/`
- **Auth**: None
- **Body**:
  ```json
  {
    "email": "string",
    "username": "string",
    "password": "string"
  }
  ```
- **Response** (201):
  ```json
  {
    "message": "User created successfully",
    "user": { "id": "uuid", "email": "string", "username": "string" },
    "tokens": { "refresh": "string", "access": "string" }
  }
  ```

### Login
- **URL**: `POST /api/users/login/`
- **Auth**: None
- **Body**:
  ```json
  { "identifier": "email | username | phone", "password": "string" }
  ```
- **Response** (200):
  ```json
  {
    "message": "Login successful",
    "user": {
      "id": "uuid",
      "email": "string",
      "username": "string",
      "is_email_verified": "boolean"
    },
    "tokens": { "refresh": "string", "access": "string" }
  }
  ```

### Logout
- **URL**: `POST /api/users/logout/`
- **Auth**: Bearer Token
- **Body**:
  ```json
  { "refresh": "string" }
  ```
- **Response** (200):
  ```json
  { "message": "Logout successful" }
  ```

### Google OAuth
- **URL**: `POST /api/users/oa/google/`
- **Auth**: None
- **Body**:
  ```json
  { "id_token": "string" }
  ```
- **Response** (200):
  ```json
  {
    "message": "Google OAuth login successful",
    "user": { "id": "uuid", "email": "string", "username": "string", "created": "boolean" },
    "tokens": { "refresh": "string", "access": "string" }
  }
  ```

---

## Password Management

### Forgot Password
- **URL**: `POST /api/users/password/forget/`
- **Auth**: None
- **Body**: `{ "email": "string" }`
- **Response** (200):
  ```json
  {
    "message": "Password reset token has been created",
    "token": "string",
    "expires_in_minutes": 60
  }
  ```

### Reset Password
- **URL**: `POST /api/users/password/reset/`
- **Auth**: None
- **Body**:
  ```json
  { "token": "string", "new_password": "string", "confirm_password": "string" }
  ```
- **Response** (200): `{ "message": "Password reset successfully" }`

### Change Password
- **URL**: `POST /api/users/password/change/`
- **Auth**: Bearer Token
- **Body**:
  ```json
  { "old_password": "string", "new_password": "string", "confirm_password": "string" }
  ```
- **Response** (200): `{ "message": "Password changed successfully" }`

---

## Two-Factor Authentication (2FA)

### Add Device
- **URL**: `POST /api/users/2fa/device/add/`
- **Auth**: Bearer Token
- **Body**: `{ "device_type": "totp | sms | email", "device_name": "string" }`
- **Response** (201):
  ```json
  {
    "message": "2FA device added successfully",
    "device": {
      "id": "integer",
      "device_type": "string",
      "device_name": "string",
      "is_verified": "boolean",
      "secret": "string (TOTP only)",
      "provisioning_uri": "string (TOTP only)"
    }
  }
  ```

### Verify Device
- **URL**: `POST /api/users/2fa/device/verify/`
- **Auth**: Bearer Token
- **Body**: `{ "device_id": "integer", "code": "string" }`
- **Response** (200):
  ```json
  {
    "message": "2FA device verified successfully",
    "device": { "id": "integer", "device_name": "string", "device_type": "string", "is_verified": true }
  }
  ```

### Remove Device
- **URL**: `POST /api/users/2fa/device/remove/`
- **Auth**: Bearer Token
- **Body**: `{ "device_id": "integer" }`
- **Response** (200): `{ "message": "Device '...' removed successfully" }`

### List Devices
- **URL**: `GET /api/users/2fa/devices/`
- **Auth**: Bearer Token
- **Response** (200):
  ```json
  {
    "devices": [
      {
        "id": "integer",
        "device_type": "string",
        "device_name": "string",
        "is_primary": "boolean",
        "is_verified": "boolean",
        "created_at": "datetime",
        "last_used_at": "datetime|null"
      }
    ],
    "total": "integer",
    "verified_count": "integer"
  }
  ```

---

## User Profile

### Get Profile
- **URL**: `GET /api/users/me/`
- **Auth**: Bearer Token
- **View**: `UserProfileView`
- **Response** (200):
  ```json
  {
    "id": "uuid",
    "email": "string",
    "username": "string",
    "phone": "string|null",
    "avatar": "string|null",
    "bio": "string",
    "timezone": "string",
    "notification_email": "boolean",
    "notification_push": "boolean",
    "is_email_verified": "boolean",
    "is_phone_verified": "boolean",
    "two_factor_enabled": "boolean",
    "capsules_sealed": "integer",
    "capsules_unlocked": "integer",
    "created_at": "datetime"
  }
  ```
- **Notes**: `capsules_sealed` and `capsules_unlocked` are computed live — not stored fields.

### Update Profile
- **URL**: `PATCH /api/users/me/update/`
- **Auth**: Bearer Token
- **View**: `UserProfileView`
- **Body** (all optional):
  ```json
  {
    "username": "string",
    "bio": "string",
    "timezone": "string",
    "notification_email": "boolean",
    "notification_push": "boolean",
    "avatar": "string"
  }
  ```
- **Response** (200): `{ "message": "Profile updated" }`

### Delete Account
- **URL**: `DELETE /api/auth/delete-account/`
- **Auth**: Bearer Token
- **View**: `DeleteAccountView`
- **Body**: `{ "password": "string" }`
- **Response** (200): `{ "message": "Account deleted" }`
- **Notes**:
  - All capsules created by the user are permanently marked `BROKEN` (pre_delete signal)
  - User removed as recipient from all other capsules
  - BROKEN capsules can never be read or unlocked by anyone

---

## Capsules

All views extend `APIView`.

### List Capsules (Vault)
- **URL**: `GET /api/capsules/`
- **Auth**: Bearer Token
- **View**: `CapsuleListCreateView`
- **Response** (200): Array of [Capsule Objects](#capsule-object)

### Create Capsule
- **URL**: `POST /api/capsules/`
- **Auth**: Bearer Token
- **View**: `CapsuleListCreateView`
- **Body**:
  ```json
  {
    "unlock_at": "datetime (required, ISO 8601)",
    "title": "string",
    "description": "string",
    "is_public": "boolean (default: false)",
    "latitude": "decimal|null",
    "longitude": "decimal|null",
    "location_name": "string",
    "unlock_radius_meters": "integer (default: 100)"
  }
  ```
- **Response** (201): [Capsule Object](#capsule-object)

### Get Capsule
- **URL**: `GET /api/capsules/:id/`
- **Auth**: Bearer Token
- **View**: `CapsuleDetailView`
- **Response** (200): [Capsule Object](#capsule-object) (with `contents` if unlocked)
- **Errors**:
  - `403` — not owner or recipient, or capsule still sealed
  - `410` — capsule is `broken`

### Delete Capsule
- **URL**: `DELETE /api/capsules/:id/`
- **Auth**: Bearer Token
- **View**: `CapsuleDetailView`
- **Response** (204): No content
- **Notes**: Owner only. Only allowed while status is `sealed`.

### Add Content
- **URL**: `POST /api/capsules/:id/contents/`
- **Auth**: Bearer Token
- **View**: `CapsuleContentView`
- **Notes**: Owner only. Capsule must be `sealed`.

**Text content** — JSON body:
```json
{ "content_type": "text", "body": "your message here" }
```

**Media content** — multipart/form-data:
| Field | Type | Required |
|-------|------|----------|
| `content_type` | `photo \| voice \| video` | Yes |
| `file` | binary | Yes |
| `duration` | integer (seconds) | No (voice/video) |

- **Response** (201):
  ```json
  { "id": "uuid", "content_type": "string", "created_at": "datetime" }
  ```
- **Notes**: Media files are encrypted before upload to S3. The raw S3 key is stored in `CapsuleContent.file` — never a local path.

### Add Recipient
- **URL**: `POST /api/capsules/:id/recipients/`
- **Auth**: Bearer Token
- **View**: `CapsuleRecipientView`
- **Body** (one of):
  ```json
  { "user_id": "uuid" }
  ```
  ```json
  { "email": "string" }
  ```
- **Response** (201): `{ "message": "Recipient added" }`
- **Notes**:
  - Owner only, capsule must be `sealed`
  - If email belongs to a registered user, linked by FK
  - Unregistered recipients stored by email; notified on unlock

### Toggle Favorite
- **URL**: `POST /api/capsules/:id/favorite/`
- **Auth**: Bearer Token
- **View**: `CapsuleFavoriteView`
- **Response**:
  - `201` `{ "favorited": true }` — just favorited
  - `200` `{ "favorited": false }` — just un-favorited
- **Errors**: `410` — capsule is broken

### Join via Share Link
- **URL**: `GET /api/capsules/join/:share_token/`
- **Auth**: Bearer Token
- **View**: `CapsuleJoinView`
- **Response** (200): [Capsule Object](#capsule-object)
- **Notes**:
  - Automatically adds the authenticated user as a recipient
  - Public capsule → `added_via = PUBLIC`; private → `added_via = LINK`
  - Content included only if capsule is already `unlocked`

### Atlas Map View
- **URL**: `GET /api/capsules/map/`
- **Auth**: Bearer Token
- **View**: `CapsuleMapView`
- **Query params** (all required):
  ```
  lat_min=float  lat_max=float  lng_min=float  lng_max=float
  ```
- **Response** (200): Array of public, location-tagged [Capsule Objects](#capsule-object) within the bounding box
- **Errors**: `400` — missing or invalid bounding box params

### Capsule Object
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "status": "sealed | unlocked | expired | broken",
  "capsule_type": "self | private | public",
  "is_public": "boolean",
  "share_token": "uuid",
  "event": "uuid|null",
  "sealed_at": "datetime",
  "unlock_at": "datetime",
  "unlocked_at": "datetime|null",
  "latitude": "decimal|null",
  "longitude": "decimal|null",
  "location_name": "string",
  "unlock_radius_meters": "integer",
  "created_at": "datetime",
  "created_by": "uuid|null",
  "contents": [
    {
      "id": "uuid",
      "content_type": "text | photo | voice | video",
      "created_at": "datetime",
      "body": "string (text only)",
      "url": "string (presigned S3 URL, media only, 15 min expiry)",
      "file_size": "integer|null",
      "duration": "integer|null (seconds)"
    }
  ]
}
```
> `contents` is only present on unlocked capsules.
> Media `url` values are pre-signed S3 GET URLs, valid for 15 minutes. Never generated for sealed or broken capsules.

---

## Discover

### Public Capsule Feed
- **URL**: `GET /api/discover/`
- **Auth**: Bearer Token
- **View**: `DiscoverView`
- **Query params** (all optional):
  | Param | Default | Description |
  |-------|---------|-------------|
  | `status` | all | Filter by capsule status (`sealed`, `unlocked`) |
  | `page` | 1 | Page number |
  | `page_size` | 20 | Results per page (max 50) |
- **Response** (200):
  ```json
  {
    "total": "integer",
    "page": "integer",
    "page_size": "integer",
    "results": [ "Capsule Objects..." ]
  }
  ```

---

## Events

### Create Event
- **URL**: `POST /api/events/`
- **Auth**: Bearer Token
- **View**: `EventListCreateView`
- **Body**:
  ```json
  {
    "title": "string (required)",
    "unlock_at": "datetime (required, ISO 8601)",
    "description": "string",
    "is_public": "boolean"
  }
  ```
- **Response** (201): [Event Object](#event-object)

### Get Event
- **URL**: `GET /api/events/:id/`
- **Auth**: Bearer Token
- **View**: `EventDetailView`
- **Response** (200): [Event Object](#event-object)

### Join Event
- **URL**: `POST /api/events/join/:invite_token/`
- **Auth**: Bearer Token
- **View**: `EventJoinView`
- **Body**:
  ```json
  { "title": "string", "description": "string" }
  ```
- **Response** (201): [Capsule Object](#capsule-object) (the user's personal capsule inside the event)
- **Notes**:
  - Creates a personal capsule linked to the event
  - `unlock_at` is forced to match the event's `unlock_at` — any client value is ignored
  - Each user can only have one capsule per event (`400` if already joined)

### List Event Capsules
- **URL**: `GET /api/events/:id/capsules/`
- **Auth**: Bearer Token
- **View**: `EventCapsulesView`
- **Response** (200): Array of [Capsule Objects](#capsule-object)
- **Notes**:
  - Before unlock: metadata for all capsules visible, but `contents` always omitted
  - After unlock: `contents` included only for the requesting user's own capsule
  - Participants can never see each other's content

### Event Object
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "created_by": "uuid|null",
  "unlock_at": "datetime",
  "invite_token": "uuid",
  "is_public": "boolean",
  "created_at": "datetime"
}
```

---

## Notifications

### List Notifications
- **URL**: `GET /api/notifications/`
- **Auth**: Bearer Token
- **View**: `NotificationListView`
- **Query params**:
  | Param | Default | Description |
  |-------|---------|-------------|
  | `unread_only` | false | Pass `true` to return only unread |
- **Response** (200): Array of Notification Objects (latest first)

### Mark Notification Read
- **URL**: `PATCH /api/notifications/:id/read/`
- **Auth**: Bearer Token
- **View**: `NotificationReadView`
- **Response** (200): `{ "message": "Marked as read" }`

### Notification Object
```json
{
  "id": "uuid",
  "type": "capsule_unlocked | recipient_added | event_joined | event_unlocked | system",
  "title": "string",
  "body": "string",
  "is_read": "boolean",
  "related_capsule": "uuid|null",
  "related_event": "uuid|null",
  "created_at": "datetime"
}
```

---

## Error Responses

All errors follow this shape:
```json
{ "error": "human-readable message" }
```

| Code | Meaning |
|------|---------|
| `400` | Bad request — missing or invalid field |
| `401` | Unauthenticated |
| `403` | Forbidden — wrong owner, wrong status, wrong password |
| `404` | Not found |
| `410` | Gone — capsule is permanently BROKEN |
| `500` | Internal server error |

---

## Resources

- [Django REST Framework](https://www.django-rest-framework.org/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [pyotp Documentation](https://github.com/pyca/pyotp)
- [Google OAuth](https://developers.google.com/identity/protocols/oauth2)

---

**Last Updated:** March 15, 2026
**Version:** 2.1
**Status:** In Development
