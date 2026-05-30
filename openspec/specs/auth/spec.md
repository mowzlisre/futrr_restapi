# auth Specification

## Purpose
Handle user authentication via username/email/phone + password, Google OAuth, JWT token management, and secure session termination.

## Requirements

### Requirement: Login with identifier
The system SHALL authenticate a user using any of: email address, username, or phone number combined with a password.

#### Scenario: Successful login
- GIVEN a registered user with a valid password
- WHEN POST /api/users/login/ with `{ identifier, password }`
- THEN return 200 with `{ message, user: { id, email, username, is_email_verified }, tokens: { access, refresh } }`

#### Scenario: Invalid credentials
- GIVEN an unrecognised identifier or wrong password
- WHEN POST /api/users/login/
- THEN return 401 with `{ error: "..." }`

---

### Requirement: Google OAuth login
The system SHALL authenticate or register a user via a Google ID token.

#### Scenario: Existing user signs in with Google
- GIVEN a user who previously registered with the same Google email
- WHEN POST /api/users/oa/google/ with `{ id_token }`
- THEN return 200 with tokens and `created: false`

#### Scenario: New user signs in with Google
- GIVEN a Google account not yet linked to any Futrr user
- WHEN POST /api/users/oa/google/ with `{ id_token }`
- THEN create a new account, return 200 with tokens and `created: true`

---

### Requirement: JWT access token refresh
The system SHALL silently renew an expired access token using the long-lived refresh token.

#### Scenario: Valid refresh token
- GIVEN a non-expired refresh token
- WHEN POST /api/token/refresh/ with `{ refresh }`
- THEN return 200 with a new `{ access }` token (5-minute TTL)

#### Scenario: Expired or invalid refresh token
- GIVEN an expired or blacklisted refresh token
- WHEN POST /api/token/refresh/
- THEN return 401; mobile client MUST clear local tokens and force re-login

---

### Requirement: Logout
The system SHALL invalidate the refresh token so it cannot be reused.

#### Scenario: Successful logout
- GIVEN an authenticated user
- WHEN POST /api/users/logout/ with `{ refresh }`
- THEN blacklist the refresh token and return 200

---

### Requirement: Legacy single-step signup
The system SHALL support registering with email + username + password in a single request.

#### Scenario: New account created
- GIVEN a unique email and username
- WHEN POST /api/users/signup/ with `{ email, username, password }`
- THEN return 201 with user object and token pair
