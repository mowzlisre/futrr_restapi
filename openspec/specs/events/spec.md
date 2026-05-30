# events Specification

## Purpose
Allow users to create time-locked group events where each participant contributes their own sealed capsule, all unlocking simultaneously on a shared date.

## Requirements

### Requirement: Create event
The system SHALL create a group event with a shared unlock date and generate a unique invite token.

#### Scenario: Valid creation
- GIVEN authenticated user with title and future unlock_at
- WHEN POST /api/events/ with `{ title, unlock_at, description?, is_public? }`
- THEN return 201 with Event object including a unique `invite_token`

---

### Requirement: Event listing
The system SHALL return a paginated list of events visible to the authenticated user.

#### Scenario: Paginated request
- GIVEN optional page and page_size query params
- WHEN GET /api/events/?page=1&page_size=20
- THEN return `{ total, page, page_size, results: [Event, ...] }`

---

### Requirement: Event slug availability
The system SHALL report whether a proposed event slug is available.

#### Scenario: Available slug
- GIVEN a slug not in use
- WHEN GET /api/events/check-slug/?slug=...
- THEN return `{ available: true, slug }`

---

### Requirement: Event detail
The system SHALL return the full event object including invite_token to the authenticated user.

#### Scenario: Known event
- GIVEN a valid event id
- WHEN GET /api/events/{id}/
- THEN return the Event object

---

### Requirement: Update event
The system SHALL allow the owner to update event metadata and banner image.

#### Scenario: Update JSON fields
- GIVEN the user is the event owner
- WHEN PATCH /api/events/{id}/ with JSON `{ title?, description?, is_public? }`
- THEN update and return 200 with the updated Event object

#### Scenario: Upload banner image
- GIVEN the user is the event owner
- WHEN PATCH /api/events/{id}/ with multipart/form-data `{ banner_image }`
- THEN upload banner to S3 and return 200 with updated Event object

---

### Requirement: Delete event
The system SHALL allow the owner to delete an event.

#### Scenario: Owner deletes event
- GIVEN the user is the event owner
- WHEN DELETE /api/events/{id}/
- THEN delete the event and return 204

---

### Requirement: Join event via invite token
The system SHALL create a personal sealed capsule for the joining user inside the event.

#### Scenario: Valid invite token, first join
- GIVEN a valid inviteToken and the user has not yet joined
- WHEN POST /api/events/join/{inviteToken}/ with `{ title?, description? }`
- THEN create a personal Capsule with unlock_at forced to the event's unlock_at, return 201 with the Capsule object
  - Note: any client-supplied unlock_at is ignored; the event's date always wins

#### Scenario: User already joined
- GIVEN the user already has a capsule in this event
- WHEN POST /api/events/join/{inviteToken}/
- THEN return 400 (duplicate join prevented)

---

### Requirement: Event capsule listing
The system SHALL list all capsules in an event with privacy rules enforced.

#### Scenario: Before unlock_at
- GIVEN current time < event.unlock_at
- WHEN GET /api/events/{id}/capsules/
- THEN return all capsule metadata (title, status, created_by, etc.) but contents ALWAYS omitted for everyone

#### Scenario: After unlock_at — own capsule
- GIVEN current time ≥ event.unlock_at and the user is the capsule owner
- WHEN GET /api/events/{id}/capsules/
- THEN return that user's capsule WITH its contents (pre-signed media URLs included)

#### Scenario: After unlock_at — other participants' capsules
- GIVEN current time ≥ event.unlock_at and the user is NOT the capsule owner
- WHEN GET /api/events/{id}/capsules/
- THEN return other participants' capsule metadata WITHOUT contents — participants never see each other's content
