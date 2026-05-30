# social Specification

## Purpose
Enable users to search for other users, follow/unfollow them, and manage incoming follow requests.

## Requirements

### Requirement: User search
The system SHALL return users whose username or email matches a search query.

#### Scenario: Matching results
- GIVEN a query string `q`
- WHEN GET /api/users/search/?q=...
- THEN return `{ results: [UserBase, ...] }` matching the query

#### Scenario: No results
- GIVEN a query with no matches
- WHEN GET /api/users/search/?q=...
- THEN return `{ results: [] }`

---

### Requirement: Public profile view
The system SHALL return the public profile of any user by UUID.

#### Scenario: Known user
- GIVEN a valid userId
- WHEN GET /api/users/{userId}/
- THEN return the UserProfile object for that user

#### Scenario: Unknown user
- GIVEN a userId that does not exist
- WHEN GET /api/users/{userId}/
- THEN return 404

---

### Requirement: Follow a user
The system SHALL allow a user to follow another user, or submit a follow request if the target account is private.

#### Scenario: Public account
- GIVEN a target user with a public account
- WHEN POST /api/users/{userId}/follow/
- THEN follow immediately and return `{ status: "following" }`

#### Scenario: Private account
- GIVEN a target user with a private account
- WHEN POST /api/users/{userId}/follow/
- THEN create a pending follow request and return `{ status: "requested" }`

---

### Requirement: Unfollow a user
The system SHALL allow a user to unfollow someone they are currently following.

#### Scenario: Currently following
- GIVEN an existing follow relationship
- WHEN DELETE /api/users/{userId}/unfollow/
- THEN remove the follow and return 200

---

### Requirement: Follow request management
The system SHALL allow a user to list, accept, or reject incoming follow requests.

#### Scenario: List follow requests
- GIVEN pending follow requests to the authenticated user
- WHEN GET /api/users/me/follow-requests/
- THEN return an array of `{ id, from_user, created_at }`

#### Scenario: Accept follow request
- GIVEN a valid requestId belonging to the authenticated user
- WHEN POST /api/users/follow-requests/{requestId}/accept/
- THEN convert the request to a follow relationship and return 200

#### Scenario: Reject follow request
- GIVEN a valid requestId belonging to the authenticated user
- WHEN DELETE /api/users/follow-requests/{requestId}/reject/
- THEN delete the request and return 200
