# user-profile Specification

## Purpose
Allow authenticated users to read and update their own profile, upload an avatar, check storage/capsule quota, and permanently delete their account.

## Requirements

### Requirement: Get own profile
The system SHALL return the full profile of the authenticated user, including computed capsule counts.

#### Scenario: Authenticated request
- GIVEN a valid access token
- WHEN GET /api/users/me/
- THEN return the full UserProfile object including `capsules_sealed` and `capsules_unlocked` (computed live, not stored)

---

### Requirement: Update profile fields
The system SHALL allow partial updates to username, bio, timezone, and notification preferences.

#### Scenario: Valid PATCH
- GIVEN any subset of `{ username, bio, timezone, notification_email, notification_push, avatar }`
- WHEN PATCH /api/users/me/update/
- THEN apply changes and return 200

---

### Requirement: Upload avatar image
The system SHALL accept a multipart avatar upload, store it in S3, and return a pre-signed URL.

#### Scenario: Valid image file
- GIVEN a multipart/form-data request with field `avatar` (JPEG/PNG/WebP)
- WHEN POST /api/users/me/avatar/
- THEN store in S3 and return `{ avatar: presigned_url }`

---

### Requirement: Quota check
The system SHALL return the user's current capsule count and storage usage against their plan limits.

#### Scenario: Quota request
- GIVEN an authenticated user
- WHEN GET /api/users/me/quota/
- THEN return `{ capsules_used, capsules_limit, storage_used_bytes, storage_limit_bytes }`

---

### Requirement: Account deletion
The system SHALL permanently delete the account after verifying the user's current password.

#### Scenario: Correct password provided
- GIVEN a valid password in the request body
- WHEN DELETE /api/auth/delete-account/ with `{ password }`
- THEN mark all the user's capsules as BROKEN (via pre_delete signal), remove the user as a recipient from all other capsules, and delete the account (200)

#### Scenario: Wrong password
- GIVEN an incorrect password
- WHEN DELETE /api/auth/delete-account/
- THEN return 403; account is NOT deleted

#### Scenario: BROKEN capsule invariant
- GIVEN that account deletion has completed
- THEN no capsule that was created by the deleted user SHALL ever be readable or unlockable, regardless of who received it
