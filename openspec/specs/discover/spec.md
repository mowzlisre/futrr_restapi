# discover Specification

## Purpose
Surface public capsules and events to authenticated users through a global feed, a friends feed (capsules from followed users), and a unified search across capsules, people, and events.

## Requirements

### Requirement: Global public feed
The system SHALL return a paginated list of public capsules (all users).

#### Scenario: Default feed
- GIVEN no filter params
- WHEN GET /api/discover/
- THEN return `{ total, page, page_size, results: [Capsule, ...] }` with public capsules, latest first

#### Scenario: Filter by status
- GIVEN status=sealed or status=unlocked
- WHEN GET /api/discover/?status=sealed
- THEN return only capsules matching that status

#### Scenario: Pagination
- GIVEN page and page_size params (max page_size=50)
- WHEN GET /api/discover/?page=2&page_size=10
- THEN return the correct page window

---

### Requirement: Friends feed
The system SHALL return a paginated feed of public capsules from users the authenticated user follows.

#### Scenario: Following users with public capsules
- GIVEN the user follows other users who have public capsules
- WHEN GET /api/discover/friends/?page=1&page_size=20
- THEN return `{ total, page, page_size, results: [Capsule, ...] }` from followed users only

#### Scenario: Not following anyone
- GIVEN the user follows no one
- WHEN GET /api/discover/friends/
- THEN return `{ total: 0, results: [] }`

---

### Requirement: Global trending feed
The system SHALL return trending public events and capsules in a single non-paginated response.

#### Scenario: Trending content exists
- GIVEN public events and capsules in the system
- WHEN GET /api/discover/global/
- THEN return `{ events: [Event, ...], capsules: [Capsule, ...] }`

---

### Requirement: Unified search
The system SHALL search across capsules, people, and events for a given query string.

#### Scenario: Query with results
- GIVEN a search term q matching capsule titles, usernames, or event titles
- WHEN GET /api/discover/search/?q=...
- THEN return `{ capsules: [...], people: [...], events: [...] }`

#### Scenario: Empty query results
- GIVEN a term matching nothing
- WHEN GET /api/discover/search/?q=...
- THEN return `{ capsules: [], people: [], events: [] }`
