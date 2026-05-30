# password Specification

## Purpose
Allow users to recover access via an OTP-gated reset flow and to change their password while authenticated.

## Requirements

### Requirement: Password reset — OTP request
The system SHALL send a one-time code to the user's registered email when they provide their identifier.

#### Scenario: Known identifier
- GIVEN an existing username or email
- WHEN POST /api/users/password/forget/ with `{ identifier }`
- THEN send an OTP to the associated email and return 200 with `{ message, expires_in_minutes: 60 }`

#### Scenario: Unknown identifier
- GIVEN an identifier not matching any account
- WHEN POST /api/users/password/forget/
- THEN return 400 (do not reveal whether the account exists)

---

### Requirement: Password reset — OTP verification
The system SHALL verify the OTP and issue a short-lived session_token to authorise the actual reset.

#### Scenario: Correct OTP
- GIVEN the correct OTP within the 60-minute window
- WHEN POST /api/users/password/verify-otp/ with `{ identifier, otp }`
- THEN return `{ session_token }` for use in /password/reset/

#### Scenario: Wrong or expired OTP
- GIVEN an incorrect or expired code
- WHEN POST /api/users/password/verify-otp/
- THEN return 400

---

### Requirement: Password reset — new password
The system SHALL update the password only when presented with a valid session_token from the OTP step.

#### Scenario: Valid session token
- GIVEN a session_token from /verify-otp/ and matching new/confirm passwords
- WHEN POST /api/users/password/reset/ with `{ identifier, session_token, new_password, confirm_password }`
- THEN update the password and return 200

#### Scenario: Mismatched passwords
- GIVEN new_password ≠ confirm_password
- WHEN POST /api/users/password/reset/
- THEN return 400

---

### Requirement: Authenticated password change
The system SHALL allow a logged-in user to change their password by supplying the current one.

#### Scenario: Correct old password
- GIVEN a valid access token and correct old_password
- WHEN POST /api/users/password/change/ with `{ old_password, new_password, confirm_password }`
- THEN update the password and return 200

#### Scenario: Wrong old password
- GIVEN an incorrect old_password
- WHEN POST /api/users/password/change/
- THEN return 403
