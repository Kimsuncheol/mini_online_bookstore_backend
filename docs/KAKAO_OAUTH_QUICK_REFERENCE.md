# KakaoTalk OAuth - Quick Reference

Fast setup guide for KakaoTalk OAuth integration.

---

## 30-Second Setup

### 1. Environment Variables

```bash
# .env file
KAKAO_CLIENT_ID=your_client_id
KAKAO_CLIENT_SECRET=your_client_secret
KAKAO_REDIRECT_URI=http://localhost:3000/auth/kakao/callback
```

### 2. Dependencies

```bash
pip install aiohttp
```

### 3. Start Server

```bash
python -m uvicorn app.main:app --reload
```

---

## API Endpoints

### Sign Up with KakaoTalk

```bash
curl -X POST http://localhost:8000/api/auth/kakao/signup \
  -H "Content-Type: application/json" \
  -d '{
    "code": "AUTH_CODE_FROM_KAKAO",
    "displayName": "Custom Name"
  }'
```

**Response (201)**:
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "displayName": "John Doe",
  "photoURL": "https://...",
  "kakaoId": "1234567890",
  "isNewUser": true,
  "message": "User signed up successfully with KakaoTalk"
}
```

### Sign In with KakaoTalk

```bash
curl -X POST http://localhost:8000/api/auth/kakao/signin \
  -H "Content-Type: application/json" \
  -d '{"code": "AUTH_CODE_FROM_KAKAO"}'
```

**Response (200)**:
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "displayName": "John Doe",
  "photoURL": "https://...",
  "kakaoId": "1234567890",
  "isNewUser": false,
  "message": "User signed in successfully with KakaoTalk"
}
```

---

## Code Examples

### Backend - Sign Up

```python
from app.services.auth_service import get_auth_service

auth_service = get_auth_service()

# Sign up with KakaoTalk
user, is_new = await auth_service.sign_up_with_kakao(
    kakao_code="AUTH_CODE",
    display_name="Optional Custom Name",
    redirect_uri="http://localhost:3000/auth/kakao/callback"
)

if is_new:
    print(f"New user: {user.email}")
else:
    print(f"Existing user linked: {user.email}")
```

### Backend - Sign In

```python
from app.services.auth_service import get_auth_service

auth_service = get_auth_service()

# Sign in with KakaoTalk
user = await auth_service.sign_in_with_kakao(
    kakao_code="AUTH_CODE",
    redirect_uri="http://localhost:3000/auth/kakao/callback"
)

print(f"Welcome back: {user.email}")
```

### Frontend - TypeScript/React

```typescript
const handleKakaoLogin = () => {
  const clientId = process.env.REACT_APP_KAKAO_CLIENT_ID;
  const redirectUri = `${window.location.origin}/auth/kakao/callback`;

  window.location.href =
    `https://kauth.kakao.com/oauth/authorize?` +
    `client_id=${clientId}&` +
    `redirect_uri=${encodeURIComponent(redirectUri)}&` +
    `response_type=code`;
};

// In callback component
useEffect(() => {
  const code = new URLSearchParams(window.location.search).get('code');

  if (code) {
    fetch('/api/auth/kakao/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    })
    .then(r => r.json())
    .then(user => {
      localStorage.setItem('user', JSON.stringify(user));
      navigate('/dashboard');
    });
  }
}, []);
```

---

## Key Features

✅ **Sign Up**: Create accounts with KakaoTalk
✅ **Sign In**: Authenticate with KakaoTalk
✅ **Email Verification**: Ensures verified KakaoTalk emails
✅ **Profile Sync**: Get name and photo from KakaoTalk
✅ **Account Linking**: Link KakaoTalk to existing accounts
✅ **Error Handling**: Graceful error messages

---

## Files Created

| File | Purpose |
|------|---------|
| `app/models/oauth.py` | OAuth request/response models |
| `app/services/kakao_oauth_service.py` | KakaoTalk API integration |
| `app/models/member.py` (updated) | Added kakao_id fields |
| `app/services/auth_service.py` (updated) | Added Kakao sign-in/up methods |
| `app/routers/auth.py` (updated) | Added Kakao endpoints |

---

## Environment Variables

| Variable | Value | Required |
|----------|-------|----------|
| `KAKAO_CLIENT_ID` | From KakaoTalk Developers | ✅ Yes |
| `KAKAO_CLIENT_SECRET` | From KakaoTalk Developers | ✅ Yes |
| `KAKAO_REDIRECT_URI` | OAuth callback URL | ❌ No (defaults to http://localhost:3000/auth/kakao/callback) |

---

## Common Errors

| Error | Fix |
|-------|-----|
| "KAKAO_CLIENT_ID not set" | Add to .env and restart server |
| "Redirect URI mismatch" | Ensure KAKAO_REDIRECT_URI matches KakaoTalk settings |
| "Email not verified" | User must verify in KakaoTalk settings |
| "User not found" | Try sign-up instead of sign-in |
| "Invalid code" | Code expired - request new authorization |

---

## Testing

### Manual Test with cURL

```bash
# 1. Get auth code from KakaoTalk
# https://kauth.kakao.com/oauth/authorize?client_id=YOUR_ID&redirect_uri=YOUR_URI&response_type=code

# 2. Test sign-up
curl -X POST http://localhost:8000/api/auth/kakao/signup \
  -H "Content-Type: application/json" \
  -d '{"code":"YOUR_CODE"}'

# 3. Test sign-in
curl -X POST http://localhost:8000/api/auth/kakao/signin \
  -H "Content-Type: application/json" \
  -d '{"code":"YOUR_CODE"}'
```

### Unit Test Example

```python
import pytest

@pytest.mark.asyncio
async def test_kakao_sign_up():
    from app.services.auth_service import get_auth_service
    auth = get_auth_service()

    user, is_new = await auth.sign_up_with_kakao("test_code")
    assert user.email is not None
    assert is_new == True

@pytest.mark.asyncio
async def test_kakao_sign_in():
    from app.services.auth_service import get_auth_service
    auth = get_auth_service()

    user = await auth.sign_in_with_kakao("test_code")
    assert user.email is not None
```

---

## Architecture at a Glance

```
KakaoTalk OAuth
    ↓
[1] User clicks "Sign in with KakaoTalk"
[2] Redirected to KakaoTalk login
[3] User authenticates
[4] Redirected back with code
[5] Frontend sends code to /api/auth/kakao/signup or /signin
[6] Backend exchanges code for access token
[7] Backend fetches user info
[8] Backend creates/finds user in database
[9] Response sent with user info
[10] Frontend stores user & navigates
```

---

## Next Steps

1. Register with [KakaoTalk Developers](https://developers.kakao.com/)
2. Create application and get credentials
3. Add environment variables to `.env`
4. Test with manual cURL requests
5. Integrate frontend OAuth flow
6. Deploy to production

---

## Documentation

**Full Guide**: [KAKAO_OAUTH_INTEGRATION.md](./KAKAO_OAUTH_INTEGRATION.md)

---

**Status**: ✅ Ready to Use
**Version**: 1.0
