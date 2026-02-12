# 🔐 Authentication Service

JWT-based authentication system with user registration, login, and token refresh capabilities.

## Features

✅ User registration with email and password  
✅ Secure password hashing (bcrypt)  
✅ JWT access tokens (1 hour expiry)  
✅ Refresh tokens (30 days expiry)  
✅ Token refresh endpoint  
✅ User logout  
✅ Get current user info  

## Architecture

```
Client → FastAPI Router → Auth Utils (JWT/Bcrypt) → In-Memory Storage
```

### Tech Stack
- **Framework**: FastAPI
- **JWT**: PyJWT
- **Password Hashing**: bcrypt
- **Storage**: In-memory (ready for database integration)

## API Endpoints

### 1. Register User
**POST** `/api/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "name": "John Doe",
      "email": "john@example.com"
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "refresh_token_here",
    "expires_at": "2026-02-12T10:30:00Z"
  }
}
```

**Errors:**
- `400 Bad Request` - Email already registered
- `500 Internal Server Error` - Registration failed

---

### 2. Login
**POST** `/api/auth/login`

Authenticate existing user and get tokens.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "name": "John Doe",
      "email": "john@example.com"
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "refresh_token_here",
    "expires_at": "2026-02-12T10:30:00Z"
  }
}
```

**Errors:**
- `401 Unauthorized` - Invalid email or password
- `500 Internal Server Error` - Login failed

---

### 3. Refresh Token
**POST** `/api/auth/refresh`

Get a new access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "refresh_token_here"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "new_jwt_token",
  "expires_at": "2026-02-12T11:30:00Z"
}
```

**Errors:**
- `401 Unauthorized` - Invalid or expired refresh token
- `500 Internal Server Error` - Token refresh failed

---

### 4. Logout
**POST** `/api/auth/logout`

Invalidate refresh token and logout user.

**Request Body:**
```json
{
  "refresh_token": "refresh_token_here"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### 5. Get Current User
**GET** `/api/auth/me`

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "user_123",
  "name": "John Doe",
  "email": "john@example.com"
}
```

**Errors:**
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - User not found

## Token Configuration

| Token Type | Expiration | Algorithm | Purpose |
|------------|-----------|-----------|---------|
| Access Token | 1 hour | HS256 | API authentication |
| Refresh Token | 30 days | Random (urlsafe) | Token renewal |

## Security Features

🔒 **Password Hashing**: bcrypt with automatic salt generation  
🔒 **JWT Signing**: HS256 algorithm with secret key  
🔒 **Token Validation**: Signature and expiration checks  
🔒 **Secure Token Storage**: Server-side refresh token management  

## Configuration

Environment variables:
```bash
JWT_SECRET_KEY=your-secret-key-change-in-production
```

## Usage Examples

### Register a User
```python
import httpx

response = httpx.post("http://localhost:8000/api/auth/register", json={
    "name": "Jane Smith",
    "email": "jane@example.com",
    "password": "SecurePass123!"
})

data = response.json()
access_token = data["data"]["access_token"]
refresh_token = data["data"]["refresh_token"]
user_id = data["data"]["user"]["id"]
```

### Login
```python
response = httpx.post("http://localhost:8000/api/auth/login", json={
    "email": "jane@example.com",
    "password": "SecurePass123!"
})

data = response.json()
access_token = data["data"]["access_token"]
```

### Make Authenticated Request
```python
headers = {"Authorization": f"Bearer {access_token}"}

response = httpx.get(
    "http://localhost:8000/api/auth/me",
    headers=headers
)

user_info = response.json()
```

### Refresh Token
```python
response = httpx.post("http://localhost:8000/api/auth/refresh", json={
    "refresh_token": refresh_token
})

data = response.json()
new_access_token = data["access_token"]
```

### Logout
```python
response = httpx.post("http://localhost:8000/api/auth/logout", json={
    "refresh_token": refresh_token
})
```

## Integration with Flash Service

The authentication system integrates with the Flash user profile system. After registration/login, you can use the `user_id` to create or manage Flash profiles:

```python
# After login, create Flash profile
flash_profile = httpx.post(
    "http://localhost:8000/api/flash/user-profile",
    json={
        "user_id": user_id,  # From auth response
        "full_name": "Jane Smith",
        "email": "jane@example.com",
        "location": "New York, NY",
        # ... other profile fields
    }
)
```

## Production Deployment

⚠️ **Before deploying to production:**

1. **Change JWT Secret Key**: Set a strong, random secret key
   ```bash
   export JWT_SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **Use Database**: Replace in-memory storage with PostgreSQL/MongoDB
   - Store users in `users` table
   - Store refresh tokens in `refresh_tokens` table

3. **Add Rate Limiting**: Prevent brute force attacks on login

4. **Enable HTTPS**: All authentication must use HTTPS

5. **Add Email Verification**: Confirm user email addresses

6. **Implement Password Reset**: Allow users to reset forgotten passwords

7. **Add 2FA (Optional)**: Two-factor authentication for enhanced security

## Error Handling

All endpoints follow consistent error responses:

```json
{
  "detail": "Error message here"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad request (validation error)
- `401` - Unauthorized (invalid credentials or token)
- `404` - Not found (user doesn't exist)
- `500` - Internal server error

## Testing

```bash
# Install dependencies
pip install PyJWT bcrypt

# Run server
uvicorn app.main:app --reload

# Test registration
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"test123456"}'

# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}'
```

## Future Enhancements

- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] Email verification
- [ ] Password reset flow
- [ ] OAuth2 social login (Google, GitHub)
- [ ] Two-factor authentication (2FA)
- [ ] Rate limiting
- [ ] Password strength validation
- [ ] Session management
- [ ] Audit logging

## License

Private project - All rights reserved
