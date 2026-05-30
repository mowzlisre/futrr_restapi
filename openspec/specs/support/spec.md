# support Specification

## Purpose
Allow authenticated users to submit in-app support tickets and track their status.

## Requirements

### Requirement: Create support ticket
The system SHALL create a support ticket associated with the authenticated user.

#### Scenario: Valid ticket submission
- GIVEN category, subject, and message are provided
- WHEN POST /api/users/support/ with `{ category, subject, message }`
- THEN create the ticket and return 201 with `{ id, message }`

---

### Requirement: List own tickets
The system SHALL return all support tickets submitted by the authenticated user.

#### Scenario: Tickets exist
- GIVEN the user has submitted one or more tickets
- WHEN GET /api/users/support/tickets/
- THEN return an array of `{ id, category, subject, status, created_at }`
  - status values: `open`, `in_progress`, `resolved`, `closed`

#### Scenario: No tickets
- GIVEN the user has not submitted any tickets
- WHEN GET /api/users/support/tickets/
- THEN return an empty array
