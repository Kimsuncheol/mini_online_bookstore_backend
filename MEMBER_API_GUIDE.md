# Member API Guide

## Overview

The Member API provides endpoints for managing user profiles, including retrieving, updating, and deleting member accounts.

## Base URL

```
http://localhost:8000/api/members
```

---

## Endpoints

### 1. Get Member Profile by ID

**Endpoint:** `GET /api/members/{member_id}`

**Description:** Retrieve a member's profile by their unique ID.

**Parameters:**
- `member_id` (path, required): The unique identifier of the member

**Response (200 OK):**
```json
{
  "id": "user_12345",
  "email": "john.doe@example.com",
  "display_name": "John Doe",
  "photo_url": "https://example.com/photos/john.jpg",
  "phone": "+1-555-123-4567",
  "address": "123 Main St, City, State 12345",
  "is_email_verified": true,
  "created_at": "2025-10-25T10:00:00.000000",
  "last_sign_in_at": "2025-10-25T14:30:00.000000",
  "preferences": {
    "email_notifications": true,
    "marketing_emails": false
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Member with ID 'user_12345' not found"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/members/user_12345
```

---

### 2. Get Member Profile by Email

**Endpoint:** `GET /api/members/email/{email}`

**Description:** Retrieve a member's profile by their email address.

**Parameters:**
- `email` (path, required): The email address of the member

**Response (200 OK):**
```json
{
  "id": "user_12345",
  "email": "john.doe@example.com",
  "display_name": "John Doe",
  "phone": "+1-555-123-4567",
  "address": "123 Main St, City, State 12345",
  "is_email_verified": true,
  "created_at": "2025-10-25T10:00:00.000000",
  "last_sign_in_at": "2025-10-25T14:30:00.000000",
  "preferences": {
    "email_notifications": true,
    "marketing_emails": false
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Member with email 'john.doe@example.com' not found"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/members/email/john.doe@example.com
```

---

### 3. Get All Members

**Endpoint:** `GET /api/members`

**Description:** Retrieve all members (with optional limit).

**Query Parameters:**
- `limit` (optional): Maximum number of members to return (1-100)

**Response (200 OK):**
```json
[
  {
    "id": "user_12345",
    "email": "john.doe@example.com",
    "display_name": "John Doe",
    "phone": "+1-555-123-4567",
    "is_email_verified": true,
    "created_at": "2025-10-25T10:00:00.000000"
  },
  {
    "id": "user_12346",
    "email": "jane.smith@example.com",
    "display_name": "Jane Smith",
    "phone": "+1-555-987-6543",
    "is_email_verified": true,
    "created_at": "2025-10-25T11:00:00.000000"
  }
]
```

**cURL Examples:**
```bash
# Get all members
curl http://localhost:8000/api/members

# Get first 10 members
curl "http://localhost:8000/api/members?limit=10"
```

---

### 4. Update Member Profile

**Endpoint:** `PATCH /api/members/{member_id}`

**Description:** Update a member's profile information.

**Parameters:**
- `member_id` (path, required): The unique identifier of the member

**Request Body (all fields optional):**
```json
{
  "display_name": "John Smith",
  "phone": "+1-555-999-8888",
  "address": "456 Oak Avenue, New City, State 54321",
  "photo_url": "https://example.com/photos/john-new.jpg",
  "preferences": {
    "email_notifications": false,
    "marketing_emails": true
  }
}
```

**Updateable Fields:**
- `email` - Email address
- `display_name` - Display name/username
- `phone` - Phone number
- `address` - Physical address
- `photo_url` - Profile photo URL
- `preferences` - Notification preferences
  - `email_notifications` - Enable/disable email notifications
  - `marketing_emails` - Enable/disable marketing emails

**Response (200 OK):**
```json
{
  "id": "user_12345",
  "email": "john.doe@example.com",
  "display_name": "John Smith",
  "phone": "+1-555-999-8888",
  "address": "456 Oak Avenue, New City, State 54321",
  "photo_url": "https://example.com/photos/john-new.jpg",
  "is_email_verified": true,
  "created_at": "2025-10-25T10:00:00.000000",
  "last_sign_in_at": "2025-10-25T14:30:00.000000",
  "preferences": {
    "email_notifications": false,
    "marketing_emails": true
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "detail": "Update data is required"
}
```

**404 Not Found:**
```json
{
  "detail": "Member with ID 'user_12345' not found"
}
```

**cURL Example:**
```bash
curl -X PATCH http://localhost:8000/api/members/user_12345 \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "John Smith",
    "phone": "+1-555-999-8888",
    "preferences": {
      "email_notifications": false,
      "marketing_emails": true
    }
  }'
```

---

### 5. Delete Account

**Endpoint:** `DELETE /api/members/{member_id}/account`

**Description:** Permanently delete a member's account from the members collection.

⚠️ **WARNING:** This action is irreversible and will permanently delete the user from the database!

**Parameters:**
- `member_id` (path, required): The unique identifier of the member to delete

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Account for member 'user_12345' has been permanently deleted",
  "deleted_email": "john.doe@example.com",
  "deleted_name": "John Doe"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "Member with ID 'user_12345' not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to delete member account"
}
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/members/user_12345/account
```

---

### 6. Get Detailed Member Profile

**Endpoint:** `GET /api/members/{member_id}/profile`

**Description:** Get comprehensive member profile information with additional metadata.

**Parameters:**
- `member_id` (path, required): The unique identifier of the member

**Response (200 OK):**
```json
{
  "id": "user_12345",
  "email": "john.doe@example.com",
  "display_name": "John Doe",
  "photo_url": "https://example.com/photos/john.jpg",
  "phone": "+1-555-123-4567",
  "address": "123 Main St, City, State 12345",
  "is_email_verified": true,
  "created_at": "2025-10-25T10:00:00.000000",
  "last_sign_in_at": "2025-10-25T14:30:00.000000",
  "preferences": {
    "email_notifications": true,
    "marketing_emails": false
  },
  "profile_complete": true
}
```

**Additional Fields:**
- `profile_complete` (boolean): Indicates if all profile fields (display_name, phone, address) are filled

**cURL Example:**
```bash
curl http://localhost:8000/api/members/user_12345/profile
```

---

## Database Structure

Members are stored in the `members` collection in Firestore:

```firestore
members/{user_id}
  ├── email: "john.doe@example.com"
  ├── display_name: "John Doe"
  ├── photo_url: "https://example.com/photos/john.jpg"
  ├── phone: "+1-555-123-4567"
  ├── address: "123 Main St, City, State 12345"
  ├── is_email_verified: true
  ├── created_at: <timestamp>
  ├── last_sign_in_at: <timestamp>
  └── preferences: {
        email_notifications: true,
        marketing_emails: false
      }
```

---

## Complete User Flow Examples

### Example 1: Get and Update Profile

```bash
# 1. Get current profile
curl http://localhost:8000/api/members/user_12345

# 2. Update phone and address
curl -X PATCH http://localhost:8000/api/members/user_12345 \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1-555-999-8888",
    "address": "456 New Street, City, State 99999"
  }'

# 3. Get updated profile
curl http://localhost:8000/api/members/user_12345/profile
```

### Example 2: Update Notification Preferences

```bash
# Disable email notifications, enable marketing emails
curl -X PATCH http://localhost:8000/api/members/user_12345 \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "email_notifications": false,
      "marketing_emails": true
    }
  }'
```

### Example 3: Delete Account Flow

```bash
# 1. Get member info before deletion (for confirmation)
curl http://localhost:8000/api/members/user_12345

# 2. Delete the account
curl -X DELETE http://localhost:8000/api/members/user_12345/account

# Response:
# {
#   "status": "success",
#   "message": "Account for member 'user_12345' has been permanently deleted",
#   "deleted_email": "john.doe@example.com",
#   "deleted_name": "John Doe"
# }

# 3. Verify deletion (should return 404)
curl http://localhost:8000/api/members/user_12345
```

---

## Validation Rules

| Field | Required | Type | Validation |
|-------|----------|------|------------|
| email | Yes | string | Valid email format |
| display_name | No | string | Max 255 characters |
| phone | No | string | Max 20 characters |
| address | No | string | No limit |
| photo_url | No | string | Valid URL format |

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request succeeded |
| 400 | Bad Request - Invalid input data |
| 404 | Not Found - Member not found |
| 500 | Internal Server Error - Server error occurred |

---

## Security Considerations

1. **Authentication:** In production, add authentication middleware to verify user identity
2. **Authorization:** Ensure users can only update/delete their own profiles
3. **Rate Limiting:** Implement rate limiting to prevent abuse
4. **Data Privacy:** Consider GDPR compliance for delete operations
5. **Soft Delete:** Consider implementing soft delete instead of hard delete
6. **Audit Log:** Keep logs of account deletions for compliance

---

## Integration with Frontend

### React/Next.js Example

```typescript
// Get member profile
async function getMemberProfile(memberId: string) {
  const response = await fetch(`http://localhost:8000/api/members/${memberId}`);
  if (!response.ok) throw new Error('Failed to fetch profile');
  return await response.json();
}

// Update member profile
async function updateMemberProfile(memberId: string, updates: Partial<Member>) {
  const response = await fetch(`http://localhost:8000/api/members/${memberId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!response.ok) throw new Error('Failed to update profile');
  return await response.json();
}

// Delete account with confirmation
async function deleteAccount(memberId: string) {
  const confirmed = confirm(
    'Are you sure you want to delete your account? This action cannot be undone!'
  );

  if (!confirmed) return;

  const response = await fetch(
    `http://localhost:8000/api/members/${memberId}/account`,
    { method: 'DELETE' }
  );

  if (!response.ok) throw new Error('Failed to delete account');
  return await response.json();
}

// Usage
updateMemberProfile('user_12345', {
  display_name: 'John Smith',
  phone: '+1-555-999-8888',
  preferences: {
    email_notifications: false,
    marketing_emails: true,
  },
})
  .then(updated => console.log('Profile updated:', updated))
  .catch(error => console.error('Error:', error));
```

---

## Testing with Interactive API Docs

FastAPI provides automatic interactive API documentation. Visit:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

You can test all member endpoints directly from your browser!

---

## Best Practices

### Before Deleting Account

1. **Confirm Intent:** Always ask for user confirmation
2. **Send Email:** Send confirmation email before deletion
3. **Grace Period:** Consider a grace period before permanent deletion
4. **Data Export:** Offer users a way to export their data first
5. **Cascade Delete:** Delete associated data (orders, reviews, cart items)

### Profile Updates

1. **Partial Updates:** Only send fields that need updating
2. **Validation:** Validate data on both client and server
3. **Optimistic UI:** Update UI optimistically, rollback on error
4. **Change Log:** Keep audit trail of profile changes

---

## Related Documentation

- [Authentication API Guide](./AUTH_API_GUIDE.md)
- [Books API Guide](./BOOKS_API_GUIDE.md)
- [Cart API Guide](./CART_API_GUIDE.md)
- [WebSocket Guide](./WEBSOCKET_GUIDE.md)

---

## Future Enhancements

- [ ] Soft delete with recovery option
- [ ] Account deactivation (temporary)
- [ ] Profile picture upload
- [ ] Email change verification
- [ ] Phone number verification
- [ ] Two-factor authentication settings
- [ ] Privacy settings management
- [ ] Account activity log
- [ ] Data export (GDPR compliance)
- [ ] Account merging
