# notifications Specification

## Purpose
Deliver and manage in-app notifications for events such as capsule unlocks, new recipients, event joins, and system messages.

## Requirements

### Requirement: List notifications
The system SHALL return notifications for the authenticated user, newest first.

#### Scenario: All notifications
- GIVEN an authenticated user with notifications
- WHEN GET /api/notifications/
- THEN return `{ total, page, page_size, results: [Notification, ...] }` sorted by created_at descending

#### Scenario: Unread-only filter
- GIVEN unread_only=true query param
- WHEN GET /api/notifications/?unread_only=true
- THEN return only notifications where is_read=false

---

### Requirement: Notification types
The system SHALL generate notifications for the following events:
- `capsule_unlocked` — a capsule the user owns or received has become unlocked
- `recipient_added` — the user has been added as a recipient to a capsule
- `event_joined` — someone has joined an event the user created
- `event_unlocked` — a group event has reached its unlock date
- `system` — platform-level announcement or administrative message

Each notification SHALL include `related_capsule` (UUID or null) and `related_event` (UUID or null) for deep linking.

---

### Requirement: Mark notification as read
The system SHALL allow marking a single notification as read.

#### Scenario: Unread notification
- GIVEN a notification with is_read=false
- WHEN PATCH /api/notifications/{id}/read/
- THEN set is_read=true and return 200 `{ message: "Marked as read" }`

#### Scenario: Already-read notification
- GIVEN a notification with is_read=true
- WHEN PATCH /api/notifications/{id}/read/
- THEN return 200 (idempotent)

#### Scenario: Other user's notification
- GIVEN a notification belonging to a different user
- WHEN PATCH /api/notifications/{id}/read/
- THEN return 404
