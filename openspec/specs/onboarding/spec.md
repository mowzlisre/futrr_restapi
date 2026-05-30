# onboarding Specification

## Purpose
Guide new users through a multi-step email-verified registration flow and capture post-registration preferences (timezone, notifications, bio) before entering the main app.

## Requirements

### Requirement: Email availability check
The system SHALL report whether an email address is already registered before the user proceeds.

#### Scenario: Available email
- GIVEN an email not linked to any account
- WHEN GET /api/users/check-email/?email=...
- THEN return `{ available: true }`

#### Scenario: Taken email
- GIVEN an email already registered
- WHEN GET /api/users/check-email/?email=...
- THEN return `{ available: false }`

---

### Requirement: Username availability check
The system SHALL report whether a username is already taken.

#### Scenario: Available username
- GIVEN a username not yet used
- WHEN GET /api/users/check-username/?username=...
- THEN return `{ available: true }`

---

### Requirement: Email OTP verification
The system SHALL send a one-time code to the email address and verify it before allowing registration.

#### Scenario: Send OTP
- GIVEN a valid email address
- WHEN POST /api/users/email/send-otp/ with `{ email }`
- THEN send an OTP to that address and return 200

#### Scenario: Verify correct OTP
- GIVEN the correct OTP code
- WHEN POST /api/users/email/verify-otp/ with `{ email, otp }`
- THEN return `{ session_token, message }` — session_token is required for /register/

#### Scenario: Incorrect or expired OTP
- GIVEN a wrong or expired code
- WHEN POST /api/users/email/verify-otp/
- THEN return 400; user must request a new OTP

---

### Requirement: Registration completion
The system SHALL create a new account only after the email has been verified via session_token.

#### Scenario: Valid session token
- GIVEN a session_token from /email/verify-otp/
- WHEN POST /api/users/register/ with `{ email, session_token, username, password }`
- THEN create the account and return 201 with `{ user, tokens: { access, refresh } }`

#### Scenario: Invalid or reused session token
- GIVEN a tampered or already-consumed session_token
- WHEN POST /api/users/register/
- THEN return 400; registration is rejected

---

### Requirement: Preboarding preferences
The system SHALL capture timezone, bio, and notification preferences after the account is created and before the user enters the main app.

#### Scenario: Complete preboarding
- GIVEN a newly registered authenticated user
- WHEN PATCH /api/users/preboarding/complete/ with `{ timezone, bio, notification_email, notification_push }`
- THEN save preferences and return 200
