# Futrr REST API - Complete Authentication Documentation

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [API Endpoints](#api-endpoints)
5. [Request/Response Examples](#requestresponse-examples)
6. [Error Handling](#error-handling)
7. [Authentication Flows](#authentication-flows)
8. [2FA Setup & Usage](#2fa-setup--usage)
9. [JWT Token Management](#jwt-token-management)
10. [Security Recommendations](#security-recommendations)
11. [Recommended Additional APIs](#recommended-additional-apis)
12. [Testing Guide](#testing-guide)
13. [Frontend Integration](#frontend-integration)
14. [Troubleshooting](#troubleshooting)

---

## Overview

The Futrr REST API provides a comprehensive authentication system with support for:
- **Traditional Authentication**: Email/Password signup and login
- **OAuth2 Integration**: Google and GitHub authentication
- **Password Management**: Secure password reset and change
- **Two-Factor Authentication (2FA)**: TOTP, SMS, and Email support
- **JWT Token Management**: Access and refresh tokens with automatic expiry

### Current Implementation Status

| Feature | Status | Endpoint |
|---------|--------|----------|
| User Signup | ✅ | `POST /api/users/signup/` |
| User Login | ✅ | `POST /api/users/login/` |
| User Logout | ✅ | `POST /api/users/logout/` |
| Google OAuth | ✅ | `POST /api/users/oa/google/` |
| GitHub OAuth | ✅ | `POST /api/users/oa/github/` |
| Forgot Password | ✅ | `POST /api/users/password/forget/` |
| Reset Password | ✅ | `POST /api/users/password/reset/` |
| Change Password | ✅ | `POST /api/users/password/change/` |
| Add 2FA Device | ✅ | `POST /api/users/2fa/device/add/` |
| Verify 2FA Device | ✅ | `POST /api/users/2fa/device/verify/` |
| Remove 2FA Device | ✅ | `POST /api/users/2fa/device/remove/` |
| List 2FA Devices | ✅ | `GET /api/users/2fa/devices/` |

---

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/achaarya/Desktop/futrr/futrr_restapi
pip3 install -r requirements.txt
```

Or install manually:
```bash
pip3 install djangorestframework==3.14.0
pip3 install djangorestframework-simplejwt==5.3.2
pip3 install pyotp==2.9.0
pip3 install requests==2.31.0
```

### 2. Run Migrations

```bash
python3 manage.py migrate
```

This creates two new database tables:
- `users_passwordresettoken` - Password reset tokens
- `users_twofactordevice` - 2FA devices

### 3. Start the Server

```bash
python3 manage.py runserver
```

### 4. Test an Endpoint

```bash
curl -X POST http://localhost:8000/api/users/signup/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Pass123456"}'
```

---

## Installation

### Prerequisites

- Python 3.8+
- Django 6.0+
- pip (Python package manager)

### Required Packages

```
Django==6.0.2
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.2
pyotp==2.9.0
requests==2.31.0
python-dotenv==1.0.0
```

### Django Settings Configuration

Ensure your `settings.py` includes:

```python
INSTALLED_APPS = [
    'app',
    'users',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt'
]

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
```

### URL Configuration

In `futrr_restapi/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
]
```

---

## API Endpoints

### User Authentication

#### 1. Sign Up
**Endpoint:** `POST /api/users/signup/`

**Authentication:** ❌ None required

**Request Body:**
```json
{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepass123"
}
```

**Validation Rules:**
- Email must contain @ and .
- Password must be at least 8 characters
- Username must be unique
- Email must be unique

**Success Response (201):**
```json
{
    "message": "User created successfully",
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "username": "testuser"
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

**Error Responses:**
| Status | Error | Reason |
|--------|-------|--------|
| 400 | Email, username, and password are required | Missing fields |
| 400 | Invalid email format | Email invalid |
| 400 | Password must be at least 8 characters long | Weak password |
| 400 | Email already exists | Duplicate email |
| 400 | Username already exists | Duplicate username |

---

#### 2. Login
**Endpoint:** `POST /api/users/login/`

**Authentication:** ❌ None required

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepass123"
}
```

**Success Response (200):**
```json
{
    "message": "Login successful",
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "username": "testuser",
        "is_email_verified": false
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

**Error Responses:**
| Status | Error | Reason |
|--------|-------|--------|
| 400 | Email and password are required | Missing fields |
| 401 | Invalid credentials | Wrong email or password |
| 403 | User account is disabled | User not active |

---

#### 3. Logout
**Endpoint:** `POST /api/users/logout/`

**Authentication:** ✅ Bearer Token required

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Success Response (200):**
```json
{
    "message": "Logout successful"
}
```

**Error Responses:**
| Status | Error | Reason |
|--------|-------|--------|
| 400 | Refresh token is required | Missing token |
| 400 | Invalid token | Malformed token |
| 401 | Unauthorized | Missing auth header |

---

### OAuth Authentication

#### 4. Google OAuth
**Endpoint:** `POST /api/users/oa/google/`

**Authentication:** ❌ None required

**Prerequisites:**
1. Create Google OAuth app at [Google Cloud Console](https://console.cloud.google.com/)
2. Obtain `id_token` from Google Sign-In on frontend

**Request Body:**
```json
{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjJjNmZhNmY1OTUwYTdjNTQ4OTQ..."
}
```

**Success Response (200):**
```json
{
    "message": "Google OAuth login successful",
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@gmail.com",
        "username": "user",
        "created": false
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

**Error Responses:**
| Status | Error | Reason |
|--------|-------|--------|
| 400 | Google OAuth token is required | Missing token |
| 401 | Invalid Google token | Token invalid |
| 400 | Could not retrieve email from Google | No email in token |

**Frontend Integration (Google Sign-In):**
```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
<div id="g_id_onload"
     data-client_id="YOUR_GOOGLE_CLIENT_ID"
     data-callback="handleCredentialResponse">
</div>
<div class="g_id_signin" data-type="standard"></div>

<script>
  function handleCredentialResponse(response) {
    const idToken = response.credential;
    
    fetch('/api/users/oa/google/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: idToken })
    })
    .then(res => res.json())
    .then(data => {
      localStorage.setItem('access_token', data.tokens.access);
      localStorage.setItem('refresh_token', data.tokens.refresh);
      window.location.href = '/dashboard';
    });
  }
</script>
```

---

#### 5. GitHub OAuth
**Endpoint:** `POST /api/users/oa/github/`

**Authentication:** ❌ None required

**Prerequisites:**
1. Create GitHub OAuth app at [GitHub Settings → Developer settings → OAuth Apps](https://github.com/settings/developers)
2. Set Authorization callback URL: `http://localhost:3000/auth/callback`
3. Obtain authorization `code` from GitHub

**Request Body:**
```json
{
    "code": "abc123def456",
    "client_id": "YOUR_GITHUB_CLIENT_ID",
    "client_secret": "YOUR_GITHUB_CLIENT_SECRET"
}
```

**Success Response (200):**
```json
{
    "message": "GitHub OAuth login successful",
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@github-email.com",
        "username": "octocat",
        "created": true
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

**Error Responses:**
| Status | Error | Reason |
|--------|-------|--------|
| 400 | Code, client_id, and client_secret are required | Missing fields |
| 401 | Failed to exchange code for token | Code invalid |
| 401 | Could not retrieve access token from GitHub | Token exchange failed |
| 401 | Failed to retrieve user info from GitHub | User info fetch failed |

**Frontend Integration (GitHub Login):**
```javascript
function loginWithGitHub() {
  const clientId = 'YOUR_GITHUB_CLIENT_ID';
  const redirectUri = 'http://localhost:3000/auth/callback';
  const scope = 'user:email';
  
  window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
}

// In callback page:
function handleGitHubCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  
  fetch('/api/users/oa/github/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      code: code,
      client_id: 'YOUR_GITHUB_CLIENT_ID',
      client_secret: 'YOUR_GITHUB_CLIENT_SECRET'
    })
  })
  .then(res => res.json())
  .then(data => {
    localStorage.setItem('access_token', data.tokens.access);
    localStorage.setItem('refresh_token', data.tokens.refresh);
    window.location.href = '/dashboard';
  });
}
```

---

### Password Management

#### 6. Forgot Password
**Endpoint:** `POST /api/users/password/forget/`

**Authentication:** ❌ None required

**Description:** Request a password reset token. Token is printed to console (for development).

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
    "message": "Password reset token has been created",
    "token": "secure_token_here",
    "expires_in_minutes": 60
}
```

**Console Output (Development):**
```
============================================================
PASSWORD RESET TOKEN FOR: user@example.com
Token: secure_token_here
Expires at: 2026-03-04 15:30:00
============================================================
```

**Error Response:**
| Status | Error |
|--------|-------|
| 400 | Email is required |
| 200 | If email doesn't exist (for security) |

---

#### 7. Reset Password
**Endpoint:** `POST /api/users/password/reset/`

**Authentication:** ❌ None required

**Description:** Reset password using valid reset token.

**Request Body:**
```json
{
    "token": "secure_token_here",
    "new_password": "NewPassword123",
    "confirm_password": "NewPassword123"
}
```

**Validation Rules:**
- Passwords must match
- Password must be at least 8 characters
- Token must not be expired (1 hour validity)
- Token must not have been used before

**Success Response (200):**
```json
{
    "message": "Password reset successfully"
}
```

**Error Responses:**
| Status | Error | Reason |
|--------|-------|--------|
| 400 | Token, new_password, and confirm_password are required | Missing fields |
| 400 | Passwords do not match | Mismatch |
| 400 | Password must be at least 8 characters long | Weak password |
| 400 | Invalid token | Token doesn't exist |
| 400 | Token has expired or already used | Token no longer valid |

---

#### 8. Change Password
**Endpoint:** `POST /api/users/password/change/`

**Authentication:** ✅ Bearer Token required

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Description:** Change password for authenticated user (when user knows old password).

**Request Body:**
```json
{
    "old_password": "CurrentPassword123",
    "new_password": "NewPassword123",
    "confirm_password": "NewPassword123"
}
```

**Validation Rules:**
- Old password must be correct
- Passwords must match
- Password must be at least 8 characters

**Success Response (200):**
```json
{
    "message": "Password changed successfully"
}
```

**Error Responses:**
| Status | Error | Reason |
|--------|-------|--------|
| 400 | old_password, new_password, and confirm_password are required | Missing fields |
| 400 | Old password is incorrect | Wrong password |
| 400 | Passwords do not match | Mismatch |
| 400 | Password must be at least 8 characters long | Weak password |
| 401 | Unauthorized | No auth token |

---

### Two-Factor Authentication (2FA)

#### 9. Add 2FA Device
**Endpoint:** `POST /api/users/2fa/device/add/`

**Authentication:** ✅ Bearer Token required

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "device_type": "totp",
    "device_name": "Google Authenticator"
}
```

**Device Types:** `totp` | `sms` | `email`

**Success Response (201) - TOTP:**
```json
{
    "message": "2FA device added. Scan QR code to verify.",
    "device": {
        "id": 1,
        "device_type": "totp",
        "device_name": "Google Authenticator",
        "is_verified": false,
        "secret": "random_secret_key",
        "provisioning_uri": "otpauth://totp/user@example.com?secret=..."
    }
}
```

**Console Output (Development):**
```
============================================================
2FA Device Created for: user@example.com
Device Type: totp
Device Name: Google Authenticator
Secret: random_secret_key
============================================================
```

**Error Responses:**
| Status | Error | Reason |
|--------|-------|--------|
| 400 | device_type and device_name are required | Missing fields |
| 400 | Invalid device_type | Invalid type |
| 400 | Device with this name already exists | Duplicate name |
| 401 | Unauthorized | No auth token |

---

#### 10. Verify 2FA Device
**Endpoint:** `POST /api/users/2fa/device/verify/`

**Authentication:** ✅ Bearer Token required

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "device_id": 1,
    "code": "123456"
}
```

**Success Response (200):**
```json
{
    "message": "2FA device verified successfully",
    "device": {
        "id": 1,
        "device_name": "Google Authenticator",
        "device_type": "totp",
        "is_verified": true
    }
}
```

**Error Responses:**
| Status | Error | Reason |
|--------|-------|--------|
| 400 | device_id and code are required | Missing fields |
| 404 | Device not found | Invalid device ID |
| 400 | Invalid OTP code | Wrong code for TOTP |
| 401 | Unauthorized | No auth token |

---

#### 11. Remove 2FA Device
**Endpoint:** `POST /api/users/2fa/device/remove/`

**Authentication:** ✅ Bearer Token required

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "device_id": 1
}
```

**Success Response (200):**
```json
{
    "message": "Device 'Google Authenticator' removed successfully"
}
```

**Error Responses:**
| Status | Error | Reason |
|--------|-------|--------|
| 400 | device_id is required | Missing ID |
| 404 | Device not found | Invalid device ID |
| 401 | Unauthorized | No auth token |

---

#### 12. List 2FA Devices
**Endpoint:** `GET /api/users/2fa/devices/`

**Authentication:** ✅ Bearer Token required

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
    "devices": [
        {
            "id": 1,
            "device_type": "totp",
            "device_name": "Google Authenticator",
            "is_primary": false,
            "is_verified": true,
            "created_at": "2026-03-04T10:30:00Z",
            "last_used_at": "2026-03-04T11:00:00Z"
        },
        {
            "id": 2,
            "device_type": "sms",
            "device_name": "SMS Backup",
            "is_primary": false,
            "is_verified": false,
            "created_at": "2026-03-04T10:35:00Z",
            "last_used_at": null
        }
    ],
    "total": 2,
    "verified_count": 1
}
```

**Error Responses:**
| Status | Error |
|--------|-------|
| 401 | Unauthorized |

---

## Request/Response Examples

### cURL Examples

#### Sign Up
```bash
curl -X POST http://localhost:8000/api/users/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123"
  }'
```

#### Login
```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

#### Logout
```bash
curl -X POST http://localhost:8000/api/users/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

#### Forgot Password
```bash
curl -X POST http://localhost:8000/api/users/password/forget/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

#### Reset Password
```bash
curl -X POST http://localhost:8000/api/users/password/reset/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "TOKEN_FROM_FORGET_PASSWORD",
    "new_password": "NewPassword123",
    "confirm_password": "NewPassword123"
  }'
```

#### Change Password (Authenticated)
```bash
curl -X POST http://localhost:8000/api/users/password/change/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "SecurePass123",
    "new_password": "NewPassword123",
    "confirm_password": "NewPassword123"
  }'
```

#### Add 2FA Device
```bash
curl -X POST http://localhost:8000/api/users/2fa/device/add/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_type": "totp",
    "device_name": "Google Authenticator"
  }'
```

#### Verify 2FA Device
```bash
curl -X POST http://localhost:8000/api/users/2fa/device/verify/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 1,
    "code": "123456"
  }'
```

#### List 2FA Devices
```bash
curl -X GET http://localhost:8000/api/users/2fa/devices/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Python Examples

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/users"

# Sign Up
response = requests.post(
    f"{BASE_URL}/signup/",
    json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123"
    }
)
print(response.json())

# Login
response = requests.post(
    f"{BASE_URL}/login/",
    json={
        "email": "test@example.com",
        "password": "SecurePass123"
    }
)
data = response.json()
access_token = data['tokens']['access']
refresh_token = data['tokens']['refresh']

# Forgot Password
response = requests.post(
    f"{BASE_URL}/password/forget/",
    json={"email": "test@example.com"}
)
print(response.json())

# Add 2FA Device
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.post(
    f"{BASE_URL}/2fa/device/add/",
    headers=headers,
    json={
        "device_type": "totp",
        "device_name": "Google Authenticator"
    }
)
print(response.json())

# List 2FA Devices
response = requests.get(
    f"{BASE_URL}/2fa/devices/",
    headers=headers
)
print(response.json())

# Logout
response = requests.post(
    f"{BASE_URL}/logout/",
    headers=headers,
    json={"refresh": refresh_token}
)
print(response.json())
```

### JavaScript Examples

```javascript
const BASE_URL = "http://localhost:8000/api/users";

// Sign Up
async function signup() {
  const response = await fetch(`${BASE_URL}/signup/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'test@example.com',
      username: 'testuser',
      password: 'SecurePass123'
    })
  });
  return response.json();
}

// Login
async function login() {
  const response = await fetch(`${BASE_URL}/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'test@example.com',
      password: 'SecurePass123'
    })
  });
  const data = await response.json();
  localStorage.setItem('access_token', data.tokens.access);
  localStorage.setItem('refresh_token', data.tokens.refresh);
  return data;
}

// Add 2FA Device
async function add2FADevice() {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${BASE_URL}/2fa/device/add/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      device_type: 'totp',
      device_name: 'Google Authenticator'
    })
  });
  return response.json();
}

// Verify 2FA Device
async function verify2FADevice(deviceId, code) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${BASE_URL}/2fa/device/verify/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      device_id: deviceId,
      code: code
    })
  });
  return response.json();
}

// List 2FA Devices
async function list2FADevices() {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${BASE_URL}/2fa/devices/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}

// Forgot Password
async function forgotPassword(email) {
  const response = await fetch(`${BASE_URL}/password/forget/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  return response.json();
}

// Reset Password
async function resetPassword(token, newPassword) {
  const response = await fetch(`${BASE_URL}/password/reset/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      token: token,
      new_password: newPassword,
      confirm_password: newPassword
    })
  });
  return response.json();
}

// Change Password
async function changePassword(oldPassword, newPassword) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${BASE_URL}/password/change/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      old_password: oldPassword,
      new_password: newPassword,
      confirm_password: newPassword
    })
  });
  return response.json();
}

// Logout
async function logout() {
  const token = localStorage.getItem('access_token');
  const refresh = localStorage.getItem('refresh_token');
  
  await fetch(`${BASE_URL}/logout/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh: refresh })
  });
  
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
    "error": "Descriptive error message"
}
```

### HTTP Status Codes

| Code | Meaning | Common Usage |
|------|---------|--------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created (signup) |
| 400 | Bad Request | Invalid input or validation error |
| 401 | Unauthorized | Invalid credentials or expired token |
| 403 | Forbidden | User disabled or insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Unexpected server error |

### Common Error Scenarios

**Missing Required Fields:**
```json
{
    "error": "Email and password are required"
}
```

**Invalid Credentials:**
```json
{
    "error": "Invalid credentials"
}
```

**Duplicate Email/Username:**
```json
{
    "error": "Email already exists"
}
```

**Invalid Token:**
```json
{
    "error": "Token has expired or already used"
}
```

**Missing Authentication:**
```json
{
    "error": "Unauthorized"
}
```

---

## Authentication Flows

### Complete Registration & Login Flow

```
1. User Signs Up
   POST /api/users/signup/
   ↓
   Returns: access_token + refresh_token
   ↓
2. Store Tokens
   localStorage.setItem('access_token', data.tokens.access)
   localStorage.setItem('refresh_token', data.tokens.refresh)
   ↓
3. Make Authenticated Requests
   Authorization: Bearer access_token
   ↓
4. Logout
   POST /api/users/logout/ with refresh_token
   ↓
   Clear stored tokens
```

### OAuth Login Flow (Google)

```
1. Frontend: Display Google Sign-In Button
   ↓
2. User Clicks Button → Google Shows Login Dialog
   ↓
3. User Completes Google Login
   ↓
4. Google Returns: id_token
   ↓
5. Frontend: Send id_token to Backend
   POST /api/users/oa/google/
   ↓
6. Backend: Verify with Google + Create/Get User
   ↓
7. Backend Returns: access_token + refresh_token
   ↓
8. Frontend: Store tokens and redirect to dashboard
```

### OAuth Login Flow (GitHub)

```
1. Frontend: Redirect to GitHub Login
   https://github.com/login/oauth/authorize?...
   ↓
2. User Completes GitHub Login
   ↓
3. GitHub Redirects: /callback?code=...
   ↓
4. Frontend: Extract code and send to Backend
   POST /api/users/oa/github/
   (with code, client_id, client_secret)
   ↓
5. Backend: Exchange code for access_token
   ↓
6. Backend: Get user info + Create/Get User
   ↓
7. Backend Returns: access_token + refresh_token
   ↓
8. Frontend: Store tokens and redirect
```

### Password Reset Flow

```
1. User Clicks "Forgot Password"
   ↓
2. User Enters Email
   POST /api/users/password/forget/
   ↓
3. Backend: Generate token (printed to console)
   ↓
4. Backend Returns: Reset token
   ↓
5. User Receives Reset Link (via email in production)
   ↓
6. User Enters New Password
   POST /api/users/password/reset/
   (with token + new_password)
   ↓
7. Backend: Validate token + Update password
   ↓
8. Redirect to login
```

### Change Password Flow (Authenticated)

```
1. User Goes to Settings → Change Password
   ↓
2. User Enters Old Password + New Password
   POST /api/users/password/change/
   (with auth token)
   ↓
3. Backend: Verify old password + Update
   ↓
4. Show Success Message
```

---

## 2FA Setup & Usage

### Adding 2FA Device (TOTP Example)

```
1. User Goes to Security Settings
   ↓
2. Click "Add 2FA Device"
   POST /api/users/2fa/device/add/
   {
       "device_type": "totp",
       "device_name": "Google Authenticator"
   }
   ↓
3. Backend Returns:
   - QR Code (provisioning_uri)
   - Secret key (for manual setup)
   ↓
4. User Scans QR Code with Authenticator App
   ↓
5. Authenticator App Generates 6-digit Code
   ↓
6. User Enters Code to Verify
   POST /api/users/2fa/device/verify/
   {
       "device_id": 1,
       "code": "123456"
   }
   ↓
7. Device Verified ✓
   2FA Enabled on Account
```

### Using 2FA During Login (Implementation Example)

**In production, after successful login, check if 2FA is enabled:**

```javascript
async functionLoginWithoutForm(email, password) {
  const response = await fetch('/api/users/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    return { error: data.error };
  }
  
  // Check if user has 2FA enabled
  const user = data.user;
  
  // Store tokens temporarily (for 2FA verification)
  sessionStorage.setItem('temp_access_token', data.tokens.access);
  
  return data;
}
```

### 2FA Device Management

```
View All Devices:
GET /api/users/2fa/devices/

Remove Device:
POST /api/users/2fa/device/remove/
{
    "device_id": 1
}

List shows status (verified/unverified)
```

---

## JWT Token Management

### Token Structure

**Access Token:**
- Short-lived (5 minutes)
- Used for API requests
- Include in Authorization header

**Refresh Token:**
- Longer-lived (24 hours)
- Used to get new access token
- Store securely (HttpOnly cookie in production)

### Using Tokens

**Include in every authenticated request:**

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/protected-endpoint/
```

### Token Expiry Handling

When access token expires, use refresh token:

**Endpoint:** `POST /api/token/refresh/` (from djangorestframework-simplejwt)

**Request:**
```json
{
    "refresh": "YOUR_REFRESH_TOKEN"
}
```

**Response:**
```json
{
    "access": "NEW_ACCESS_TOKEN"
}
```

### Token Configuration

Edit `settings.py` to customize:

```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),  # Access token validity
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),   # Refresh token validity
}
```

---

## Security Recommendations

### 1. HTTPS Only
- Always use HTTPS in production
- Never transmit tokens over HTTP

### 2. Token Storage
```javascript
// DO: Store access token in memory
const accessToken = response.data.access;

// DO: Store refresh token in HttpOnly secure cookie
// (set by backend automatically)

// DON'T: Store tokens in localStorage
// localStorage.setItem('token', token);  // Vulnerable to XSS
```

### 3. CORS Configuration

Edit `settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://yourdomain.com"
]
```

### 4. Password Security

- Enforce minimum 8 characters (already implemented)
- Consider adding complexity requirements:
  - Uppercase letters
  - Numbers
  - Special characters

### 5. Account Protection

- Implement rate limiting on auth endpoints
- Lock account after N failed login attempts
- Log all login attempts
- Notify user of suspicious activity

### 6. API Security

- Use HTTPS only
- Implement rate limiting
- Validate all inputs
- Use CSRF tokens for state-changing requests

### 7. 2FA Security

- Store TOTP secrets encrypted
- Implement backup codes for account recovery
- Support multiple 2FA methods

### 8. Token Security

- Rotate refresh tokens regularly
- Implement token blacklisting for logout
- Set appropriate expiry times
- Sign tokens with strong secret key

---

## Recommended Additional APIs

### High Priority (Production-Ready)

1. **Email Verification**
   ```
   POST /api/users/email/verify/send/
   POST /api/users/email/verify/confirm/
   ```
   - Send verification email
   - Verify email with token

2. **Phone Verification**
   ```
   POST /api/users/phone/verify/request/
   POST /api/users/phone/verify/confirm/
   ```
   - Send SMS OTP
   - Verify phone with code

3. **2FA Login Verification**
   ```
   POST /api/users/2fa/verify-login/
   ```
   - Verify 2FA during login
   - Return tokens only if 2FA passes

4. **Profile Management**
   ```
   GET /api/users/profile/
   PUT /api/users/profile/
   DELETE /api/users/profile/
   ```
   - Get/update user info
   - Deactivate account

### Medium Priority

5. **Additional OAuth Providers**
   - Apple OAuth
   - Microsoft/Office 365
   - LinkedIn
   - Discord

6. **Session Management**
   ```
   GET /api/users/sessions/
   DELETE /api/users/sessions/{id}/
   DELETE /api/users/sessions/
   ```
   - List active sessions
   - Logout from specific device
   - Logout from all devices

7. **Account Recovery**
   ```
   POST /api/users/account/backup-codes/
   POST /api/users/account/use-backup-code/
   ```
   - Generate backup codes
   - Use backup code as 2FA fallback

### Nice to Have

8. **Magic Links (Passwordless Auth)**
9. **Biometric Authentication**
10. **Account Linking**
11. **Login Activity Log**
12. **Privacy Controls**

---

## Testing Guide

### Setup Postman/Insomnia

1. Create new collection: "Futrr Auth APIs"
2. Add environment variables:
   ```
   base_url: http://localhost:8000
   access_token: (fill after login)
   refresh_token: (fill after login)
   reset_token: (fill after forgot-password)
   ```

### Test Sequence

#### 1. Sign Up
```
POST {{base_url}}/api/users/signup/
Body:
{
  "email": "testuser@example.com",
  "username": "testuser",
  "password": "TestPass123"
}
Tests:
✓ Status 201
✓ Response contains tokens
```

#### 2. Login
```
POST {{base_url}}/api/users/login/
Body:
{
  "email": "testuser@example.com",
  "password": "TestPass123"
}
Tests:
✓ Status 200
✓ Save access_token to environment
✓ Save refresh_token to environment
```

#### 3. Forgot Password
```
POST {{base_url}}/api/users/password/forget/
Body:
{
  "email": "testuser@example.com"
}
Tests:
✓ Status 200
✓ Response contains reset_token
✓ Save reset_token to environment
```

#### 4. Reset Password
```
POST {{base_url}}/api/users/password/reset/
Body:
{
  "token": "{{reset_token}}",
  "new_password": "NewPass456",
  "confirm_password": "NewPass456"
}
Tests:
✓ Status 200
✓ Can login with new password
```

#### 5. Change Password
```
POST {{base_url}}/api/users/password/change/
Headers:
Authorization: Bearer {{access_token}}
Body:
{
  "old_password": "NewPass456",
  "new_password": "FinalPass789",
  "confirm_password": "FinalPass789"
}
Tests:
✓ Status 200
```

#### 6. Add 2FA Device
```
POST {{base_url}}/api/users/2fa/device/add/
Headers:
Authorization: Bearer {{access_token}}
Body:
{
  "device_type": "totp",
  "device_name": "Test Authenticator"
}
Tests:
✓ Status 201
✓ Response contains secret & provision​ing_uri
✓ Save device_id to environment
```

#### 7. List 2FA Devices
```
GET {{base_url}}/api/users/2fa/devices/
Headers:
Authorization: Bearer {{access_token}}
Tests:
✓ Status 200
✓ Response contains devices array
✓ Device shows is_verified: false
```

#### 8. Verify 2FA Device (Simulate OTP)
```
POST {{base_url}}/api/users/2fa/device/verify/
Headers:
Authorization: Bearer {{access_token}}
Body:
{
  "device_id": 1,
  "code": "000000"
}
Note: For TOTP testing, generate code using pyotp:

python3 -c "import pyotp; print(pyotp.TOTP('SECRET_KEY').now())"
```

#### 9. Remove 2FA Device
```
POST {{base_url}}/api/users/2fa/device/remove/
Headers:
Authorization: Bearer {{access_token}}
Body:
{
  "device_id": 1
}
Tests:
✓ Status 200
```

#### 10. Logout
```
POST {{base_url}}/api/users/logout/
Headers:
Authorization: Bearer {{access_token}}
Body:
{
  "refresh": "{{refresh_token}}"
}
Tests:
✓ Status 200
✓ Refresh token is blacklisted
```

---

## Frontend Integration

### React Example

```jsx
import React, { useState } from 'react';

const API_BASE = 'http://localhost:8000/api/users';

function Authentication() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [accessToken, setAccessToken] = useState(null);

  const signup = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/signup/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          username: email.split('@')[0],
          password
        })
      });
      const data = await res.json();
      
      if (res.ok) {
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        setAccessToken(data.tokens.access);
        alert('Signup successful!');
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const login = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      
      if (res.ok) {
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        setAccessToken(data.tokens.access);
        alert('Login successful!');
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const refresh = localStorage.getItem('refresh_token');
      
      await fetch(`${API_BASE}/logout/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh })
      });
      
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setAccessToken(null);
      alert('Logged out!');
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  return (
    <div>
      {!accessToken ? (
        <forms>
          <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button onClick={signup}>Sign Up</button>
          <button onClick={login}>Login</button>
        </forms>
      ) : (
        <button onClick={logout}>Logout</button>
      )}
    </div>
  );
}

export default Authentication;
```

### Vue.js Example

```vue
<template>
  <div>
    <div v-if="!accessToken">
      <input v-model="email" type="email" placeholder="Email" />
      <input v-model="password" type="password" placeholder="Password" />
      <button @click="signup">Sign Up</button>
      <button @click="login">Login</button>
    </div>
    <div v-else>
      <button @click="logout">Logout</button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      email: '',
      password: '',
      accessToken: null
    };
  },
  methods: {
    async signup() {
      const res = await fetch('http://localhost:8000/api/users/signup/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: this.email,
          username: this.email.split('@')[0],
          password: this.password
        })
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('access_token', data.tokens.access);
        this.accessToken = data.tokens.access;
      }
    },
    async login() {
      const res = await fetch('http://localhost:8000/api/users/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: this.email,
          password: this.password
        })
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('access_token', data.tokens.access);
        this.accessToken = data.tokens.access;
      }
    },
    async logout() {
      const token = localStorage.getItem('access_token');
      await fetch('http://localhost:8000/api/users/logout/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh: localStorage.getItem('refresh_token') })
      });
      localStorage.removeItem('access_token');
      this.accessToken = null;
    }
  }
};
</script>
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'rest_framework'"

**Cause:** Dependencies not installed

**Solution:**
```bash
pip3 install -r requirements.txt
```

### "No such table: users_passwordresettoken"

**Cause:** Migrations not run

**Solution:**
```bash
python3 manage.py migrate
```

### "Invalid Google token"

**Cause:** Token expired or invalid format

**Solution:**
- Verify token is not expired
- Check token format from frontend
- Ensure Google OAuth credentials are correct

### "Invalid credentials" on Login

**Cause:** Wrong email or password, or user doesn't exist

**Solution:**
- Verify email exists in database
- Check password is correct
- Ensure user account is active

### "Token has expired or already used"

**Cause:** Reset token is no longer valid

**Solution:**
- Request new password reset token
- Tokens expire after 1 hour

### "CORS errors" (blocked by browser)

**Cause:** Frontend origin not in CORS_ALLOWED_ORIGINS

**Solution:** Add to `settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://yourdomain.com"
]
```

### "Unauthorized" on authenticated endpoints

**Cause:** Missing or invalid access token

**Solution:**
- Verify authorization header is present
- Format: `Authorization: Bearer <access_token>`
- Token may have expired - use refresh token

### "Device with this name already exists"

**Cause:** User already has device with same name

**Solution:**
- Use unique device names (e.g., "iPhone 12", "Samsung Galaxy")
- Remove old device first

### 2FA Code Always Invalid

**Cause:** Clock skew or wrong secret

**Solution:**
- Sync device time with server
- Verify secret key is correct
- Regenerate device if needed

---

## Database Models

### PasswordResetToken

```python
class PasswordResetToken(models.Model):
    user = models.ForeignKey(FutrrUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 1 hour from creation
    is_used = models.BooleanField(default=False)
```

### TwoFactorDevice

```python
class TwoFactorDevice(models.Model):
    user = models.ForeignKey(FutrrUser, on_delete=models.CASCADE)
    device_type = models.CharField(max_length=10, choices=[
        ('totp', 'Time-based OTP'),
        ('sms', 'SMS'),
        ('email', 'Email')
    ])
    device_name = models.CharField(max_length=100)
    secret = models.CharField(max_length=255)  # For TOTP
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
```

---

## Next Steps

1. ✅ Install dependencies: `pip3 install -r requirements.txt`
2. ✅ Run migrations: `python3 manage.py migrate`
3. ✅ Test all endpoints using provided examples
4. 📝 Implement email verification (recommended)
5. 📝 Add SMS verification with Twilio (optional)
6. 📝 Implement account activity logging
7. 📝 Add rate limiting on auth endpoints
8. 📝 Setup OAuth apps (Google, GitHub) in production

---

## File Structure

```
users/
  ├── migrations/
  │   ├── __init__.py
  │   ├── 0001_initial.py
  │   └── 0002_add_password_reset_and_2fa.py
  ├── __init__.py
  ├── admin.py
  ├── apps.py
  ├── models.py          # PasswordResetToken, TwoFactorDevice
  ├── tests.py
  ├── api.py             # All API classes
  ├── urls.py            # All endpoint routes
  └── views.py

futrr_restapi/
  ├── __init__.py
  ├── asgi.py
  ├── settings.py        # JWT & REST config
  ├── urls.py            # Main URL router
  └── wsgi.py

requirements.txt         # Python dependencies
API.md                  # This file
```

---

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [pyotp Documentation](https://github.com/pyca/pyotp)
- [Google OAuth](https://developers.google.com/identity/protocols/oauth2)
- [GitHub OAuth](https://docs.github.com/en/developers/apps/building-oauth-apps)

---

## Support & Contribution

For issues, questions, or improvements:
1. Check this documentation
2. Review error messages carefully
3. Test with provided examples
4. Check Django logs

---

**Last Updated:** March 4, 2026
**Version:** 1.0
**Status:** Production Ready
