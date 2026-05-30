# two-factor-auth Specification

## Purpose
Allow users to enrol, verify, and remove two-factor authentication devices (TOTP, SMS, or email) to add a second layer of security to their account.

## Requirements

### Requirement: Add a 2FA device
The system SHALL register a new 2FA device and return setup credentials.

#### Scenario: Add TOTP device
- GIVEN an authenticated user
- WHEN POST /api/users/2fa/device/add/ with `{ device_type: "totp", device_name }`
- THEN return 201 with the device record plus `secret` and `provisioning_uri` (otpauth:// for QR code scanning)

#### Scenario: Add email or SMS device
- GIVEN an authenticated user
- WHEN POST /api/users/2fa/device/add/ with `{ device_type: "email" | "sms", device_name }`
- THEN return 201 with device record (no secret or provisioning_uri)

---

### Requirement: Verify a 2FA device
The system SHALL mark a device as verified only after the user supplies a valid one-time code.

#### Scenario: Correct code
- GIVEN an unverified device_id and the correct OTP
- WHEN POST /api/users/2fa/device/verify/ with `{ device_id, code }`
- THEN set is_verified=true and return 200

#### Scenario: Wrong code
- GIVEN an incorrect OTP
- WHEN POST /api/users/2fa/device/verify/
- THEN return 400 without changing verification state

---

### Requirement: Remove a 2FA device
The system SHALL allow a user to unlink a 2FA device from their account.

#### Scenario: Remove existing device
- GIVEN a valid device_id owned by the authenticated user
- WHEN POST /api/users/2fa/device/remove/ with `{ device_id }`
- THEN delete the device and return 200

---

### Requirement: List 2FA devices
The system SHALL return all 2FA devices registered to the authenticated user.

#### Scenario: Devices exist
- GIVEN one or more registered devices
- WHEN GET /api/users/2fa/devices/
- THEN return `{ devices: [...], total, verified_count }`

#### Scenario: No devices registered
- GIVEN no 2FA devices on the account
- WHEN GET /api/users/2fa/devices/
- THEN return `{ devices: [], total: 0, verified_count: 0 }`
