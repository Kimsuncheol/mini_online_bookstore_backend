# Authentication API Guide

## Overview

The Authentication API provides endpoints for user registration, sign-out, and session management.

## Base URL

```
http://localhost:8000/api/auth
```

---

## Endpoints

### 1. Sign Up

**Endpoint:** `POST /api/auth/signup`

**Description:** Register a new user by creating a member record with email and display name.

**Request Body:**
```json
{
  "email": "user@example.com",
  "display_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "id": "user_12345",
  "email": "user@example.com",
  "display_name": "John Doe",
  "message": "User signed up successfully"
}
```

**Error Responses:**

**400 Bad Request** (Email already exists):
```json
{
  "detail": "User with email 'user@example.com' already exists"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error signing up user: {error_message}"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "display_name": "John Doe"
  }'
```

---

### 2. Sign Out

**Endpoint:** `POST /api/auth/signout`

**Description:** Sign out a user by invalidating their session.

**Query Parameters:**
- `user_id` (required): The ID of the user to sign out

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "User 'user_12345' signed out successfully"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "User with ID 'user_12345' not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error signing out user: {error_message}"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/auth/signout?user_id=user_12345"
```

---

### 3. Get Session Info

**Endpoint:** `GET /api/auth/session/{user_id}`

**Description:** Get detailed information about a user's current session.

**Parameters:**
- `user_id` (path, required): The ID of the user

**Response (200 OK):**
```json
{
  "user_id": "user_12345",
  "is_signed_in": true,
  "created_at": "2025-10-25T10:00:00.000000",
  "last_sign_in_at": "2025-10-25T14:30:00.000000",
  "last_sign_out_at": "2025-10-25T12:00:00.000000"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "User with ID 'user_12345' not found"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/auth/session/user_12345
```

---

### 4. Verify Session

**Endpoint:** `GET /api/auth/session/{user_id}/verify`

**Description:** Verify if a user has an active session.

**Parameters:**
- `user_id` (path, required): The ID of the user

**Response (200 OK):**
```json
{
  "user_id": "user_12345",
  "is_active": true,
  "message": "Session is active"
}
```

**Or if not active:**
```json
{
  "user_id": "user_12345",
  "is_active": false,
  "message": "Session is not active"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/auth/session/user_12345/verify
```

---

## Sign-Up Process Details

### What Happens When a User Signs Up

1. **Email Validation:** Checks if the email is already registered
2. **Member Creation:** Creates a new document in the `members` collection with:
   - `email`: User's email address
   - `display_name`: User's display name/username
   - `photo_url`: `null` (can be updated later)
   - `phone`: `null` (can be updated later)
   - `address`: `null` (can be updated later)
   - `is_email_verified`: `false`
   - `created_at`: Current timestamp
   - `last_sign_in_at`: Current timestamp
   - `is_signed_in`: `true`
   - `preferences`: Default preferences object

3. **Default Preferences:**
   ```json
   {
     "email_notifications": true,
     "marketing_emails": false
   }
   ```

4. **Return:** Returns the created member with a unique ID

---

## Database Structure

### Members Collection

When a user signs up, a new document is created in the `members` collection:

```firestore
members/{user_id}
  - email: "john.doe@example.com"
  - display_name: "John Doe"
  - photo_url: null
  - phone: null
  - address: null
  - is_email_verified: false
  - created_at: <timestamp>
  - last_sign_in_at: <timestamp>
  - is_signed_in: true
  - preferences: {
      email_notifications: true,
      marketing_emails: false
    }
```

---

## Complete User Flow Example

### 1. New User Registration

```bash
# Step 1: Sign up
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "display_name": "Alice Smith"
  }'

# Response:
# {
#   "id": "user_abc123",
#   "email": "alice@example.com",
#   "display_name": "Alice Smith",
#   "message": "User signed up successfully"
# }
```

### 2. Check Session

```bash
# Step 2: Verify the user is signed in
curl http://localhost:8000/api/auth/session/user_abc123/verify

# Response:
# {
#   "user_id": "user_abc123",
#   "is_active": true,
#   "message": "Session is active"
# }
```

### 3. Get Full Session Info

```bash
# Step 3: Get detailed session information
curl http://localhost:8000/api/auth/session/user_abc123

# Response:
# {
#   "user_id": "user_abc123",
#   "is_signed_in": true,
#   "created_at": "2025-10-25T10:00:00.000000",
#   "last_sign_in_at": "2025-10-25T10:00:00.000000",
#   "last_sign_out_at": null
# }
```

### 4. Sign Out

```bash
# Step 4: Sign out the user
curl -X POST "http://localhost:8000/api/auth/signout?user_id=user_abc123"

# Response:
# {
#   "status": "success",
#   "message": "User 'user_abc123' signed out successfully"
# }
```

### 5. Verify Session After Sign-Out

```bash
# Step 5: Verify session is now inactive
curl http://localhost:8000/api/auth/session/user_abc123/verify

# Response:
# {
#   "user_id": "user_abc123",
#   "is_active": false,
#   "message": "Session is not active"
# }
```

---

## Validation Rules

| Field | Required | Type | Validation |
|-------|----------|------|------------|
| email | Yes | string | Valid email format |
| display_name | Yes | string | 1-255 characters |

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request succeeded |
| 201 | Created - User created successfully |
| 400 | Bad Request - Invalid input or email already exists |
| 404 | Not Found - User not found |
| 500 | Internal Server Error - Server error occurred |

---

## Error Handling

### Common Errors

**Duplicate Email:**
```json
{
  "detail": "User with email 'user@example.com' already exists"
}
```

**Invalid Email Format:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address"
    }
  ]
}
```

**Missing Required Field:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "display_name"],
      "msg": "Field required"
    }
  ]
}
```

---

## Security Considerations

1. **Email Validation:** Always validate email format
2. **Duplicate Prevention:** Check for existing emails before creating users
3. **Password:** This implementation does not handle passwords - integrate with Firebase Authentication or another auth provider for password management
4. **Session Management:** Use secure tokens in production (JWT, OAuth)
5. **HTTPS:** Always use HTTPS in production
6. **Rate Limiting:** Implement rate limiting to prevent abuse

---

## Integration with Frontend

### React/Next.js Example

```typescript
// Sign up function
async function signUp(email: string, displayName: string) {
  try {
    const response = await fetch('http://localhost:8000/api/auth/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        display_name: displayName,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    const data = await response.json();
    console.log('User signed up:', data);

    // Store user ID in localStorage or state management
    localStorage.setItem('userId', data.id);

    return data;
  } catch (error) {
    console.error('Sign up error:', error);
    throw error;
  }
}

// Usage
signUp('alice@example.com', 'Alice Smith')
  .then(user => {
    console.log('Success:', user);
    // Redirect to dashboard or home page
  })
  .catch(error => {
    console.error('Failed:', error.message);
    // Show error to user
  });
```

---

## Testing with Interactive API Docs

FastAPI provides automatic interactive API documentation. Visit:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

You can test all authentication endpoints directly from your browser!

---

## Next Steps

After implementing basic sign-up, consider adding:

1. **Password Authentication:** Integrate Firebase Authentication
2. **Email Verification:** Send verification emails
3. **Password Reset:** Implement forgot password flow
4. **OAuth:** Add Google, Facebook, GitHub login
5. **JWT Tokens:** Implement token-based authentication
6. **Refresh Tokens:** Add token refresh mechanism
7. **2FA:** Two-factor authentication
8. **Account Deletion:** Allow users to delete their accounts

---

## Related Documentation

- [Member API Guide](./IMPLEMENTATION_SUMMARY.md)
- [WebSocket Guide](./WEBSOCKET_GUIDE.md)
- [Cart API Guide](./CART_API_GUIDE.md)
- [Books API Guide](./BOOKS_API_GUIDE.md)
