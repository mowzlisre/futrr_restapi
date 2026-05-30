# capsules Specification

## Purpose
Manage the full lifecycle of time-locked memory capsules: creation, content attachment (text/photo/voice/video with S3 encryption), recipient management, time-locked unlocking, geolocation, favorites, and sharing via deep link.

## Requirements

### Requirement: Capsule lifecycle states
The system SHALL enforce that every capsule is in exactly one of four states: `sealed`, `unlocked`, `expired`, or `broken`.

#### Scenario: State transitions
- `sealed` → `unlocked` when unlock_at is reached and unlock is triggered
- `sealed` → `expired` if the capsule was never unlocked past its expiry window
- Any state → `broken` if the owner's account is deleted (irreversible)
- `broken` capsules SHALL never be read, unlocked, or have contents served

---

### Requirement: List own capsules (Vault)
The system SHALL return all capsules created by or addressed to the authenticated user.

#### Scenario: Vault load
- GIVEN an authenticated user
- WHEN GET /api/capsules/
- THEN return an array of Capsule objects (own + received)

---

### Requirement: Create capsule
The system SHALL create a sealed capsule with a mandatory future unlock date.

#### Scenario: Valid creation
- GIVEN a valid ISO 8601 unlock_at in the future
- WHEN POST /api/capsules/ with `{ unlock_at, title?, description?, is_public?, latitude?, longitude?, location_name?, unlock_radius_meters? }`
- THEN return 201 with the new Capsule object (status=sealed)

---

### Requirement: Capsule detail
The system SHALL return a capsule's metadata and contents based on the requester's access and the capsule's state.

#### Scenario: Owner or recipient, capsule is sealed
- GIVEN status=sealed and the user is the owner or a recipient
- WHEN GET /api/capsules/{id}/
- THEN return capsule metadata WITHOUT contents array

#### Scenario: Owner or recipient, capsule is unlocked
- GIVEN status=unlocked and the user is the owner or a recipient
- WHEN GET /api/capsules/{id}/
- THEN return capsule metadata WITH contents array (media items include pre-signed S3 URLs, 15-minute expiry)

#### Scenario: Non-participant requests the capsule
- GIVEN the user is neither owner nor a recipient
- WHEN GET /api/capsules/{id}/
- THEN return 403

#### Scenario: BROKEN capsule
- GIVEN status=broken
- WHEN GET /api/capsules/{id}/
- THEN return 410 Gone

---

### Requirement: Delete capsule
The system SHALL allow the owner to delete a sealed capsule only.

#### Scenario: Owner deletes sealed capsule
- GIVEN status=sealed and the user is the owner
- WHEN DELETE /api/capsules/{id}/
- THEN delete the capsule and return 204

#### Scenario: Attempt to delete unlocked capsule
- GIVEN status=unlocked
- WHEN DELETE /api/capsules/{id}/
- THEN return 403

---

### Requirement: Add content to capsule
The system SHALL allow the owner to attach text, photo, voice, or video content to a sealed capsule.

#### Scenario: Text content
- GIVEN status=sealed and user is owner
- WHEN POST /api/capsules/{id}/contents/ with JSON `{ content_type: "text", body }`
- THEN store the text and return 201

#### Scenario: Media content (photo/voice/video)
- GIVEN status=sealed and user is owner
- WHEN POST /api/capsules/{id}/contents/ with multipart/form-data `{ content_type, file, duration? }`
- THEN encrypt the file before upload to S3, store the S3 key in CapsuleContent.file (never a local path), and return 201

#### Scenario: Non-owner attempts to add content
- GIVEN user is NOT the capsule owner
- WHEN POST /api/capsules/{id}/contents/
- THEN return 403

---

### Requirement: Recipient management
The system SHALL allow the owner to add and remove recipients from a sealed capsule.

#### Scenario: Add recipient by user_id
- GIVEN status=sealed, user is owner, and the target user exists
- WHEN POST /api/capsules/{id}/recipients/ with `{ user_id }`
- THEN link the user as a recipient and return 201

#### Scenario: Add recipient by email (unregistered user)
- GIVEN status=sealed, user is owner, and the email is not registered
- WHEN POST /api/capsules/{id}/recipients/ with `{ email }`
- THEN store the email as a pending recipient; notify on unlock

#### Scenario: Remove recipient
- GIVEN status=sealed and user is owner
- WHEN DELETE /api/capsules/{id}/recipients/{recipientId}/
- THEN remove the recipient and return 204

---

### Requirement: Toggle favorite
The system SHALL allow any user to favorite or un-favorite a capsule they can see.

#### Scenario: First favorite
- GIVEN the user has NOT previously favorited this capsule
- WHEN POST /api/capsules/{id}/favorite/
- THEN create the favorite and return 201 `{ favorited: true }`

#### Scenario: Un-favorite
- GIVEN the user HAS previously favorited this capsule
- WHEN POST /api/capsules/{id}/favorite/
- THEN remove the favorite and return 200 `{ favorited: false }`

#### Scenario: BROKEN capsule
- GIVEN status=broken
- WHEN POST /api/capsules/{id}/favorite/
- THEN return 410

---

### Requirement: Capsule unlock
The system SHALL unlock a capsule and serve its contents when unlock_at has passed.

#### Scenario: Past unlock time
- GIVEN current time ≥ unlock_at
- WHEN POST /api/capsules/{id}/unlock/
- THEN set status=unlocked, return 200 with full Capsule object including contents

#### Scenario: Before unlock time
- GIVEN current time < unlock_at
- WHEN POST /api/capsules/{id}/unlock/
- THEN return 403

---

### Requirement: Visibility and location settings
The system SHALL allow the owner to update whether a capsule appears in public feeds and the Atlas map.

#### Scenario: Make capsule public and add to Atlas
- GIVEN a capsule with valid coordinates
- WHEN PATCH /api/capsules/{id}/visibility/ with `{ is_public: true, listed_in_atlas: true, latitude, longitude, location_name }`
- THEN update settings and return 200

---

### Requirement: Invitation accept/decline
The system SHALL allow a recipient to explicitly accept or decline a received capsule invitation.

#### Scenario: Accept invitation
- GIVEN the user is an invited recipient
- WHEN POST /api/capsules/{id}/invitation/
- THEN mark as accepted and return 200

#### Scenario: Decline invitation
- GIVEN the user is an invited recipient
- WHEN DELETE /api/capsules/{id}/invitation/
- THEN remove the recipient record and return 200

---

### Requirement: Join via share link
The system SHALL automatically add the authenticated user as a recipient when they visit a share link.

#### Scenario: Public capsule share link
- GIVEN a valid shareToken for a public capsule
- WHEN GET /api/capsules/join/{shareToken}/
- THEN add user as recipient with added_via=PUBLIC and return the Capsule object

#### Scenario: Private capsule share link
- GIVEN a valid shareToken for a private capsule
- WHEN GET /api/capsules/join/{shareToken}/
- THEN add user as recipient with added_via=LINK and return the Capsule object

---

### Requirement: Atlas map view
The system SHALL return public, location-tagged, sealed capsules within a geographic bounding box.

#### Scenario: Valid bounding box
- GIVEN all four params: lat_min, lat_max, lng_min, lng_max
- WHEN GET /api/capsules/map/?lat_min=&lat_max=&lng_min=&lng_max=&limit=50
- THEN return an array of public capsules within the box

#### Scenario: Missing bounding box params
- GIVEN any of the four required params is absent
- WHEN GET /api/capsules/map/
- THEN return 400

---

### Requirement: Favorites list
The system SHALL return all capsules the user has favorited.

#### Scenario: Favorites exist
- GIVEN one or more favorited capsules
- WHEN GET /api/capsules/favorites/
- THEN return an array of Capsule objects
