# Flash Service - Consolidated API Reference

**All-in-One Service:** Authentication + AI Job Assistant in a single service!

## 🚀 Quick Start

```bash
# Start the service
uvicorn app.main:app --reload --port 8000

# All endpoints available at /api/flash/*
```

## 📍 Endpoint Structure

### Old Architecture (2 Services):
```
/api/auth/register      ❌ Separate auth service
/api/auth/login         ❌ Separate auth service
/api/flash/user-profile ❌ Separate services
```

### New Architecture (1 Service):
```
/api/flash/auth/register        ✅ All in Flash!
/api/flash/auth/login           ✅ All in Flash!
/api/flash/user-profile         ✅ All in Flash!
/api/flash/analyze-job          ✅ All in Flash!
```

## 🔐 Authentication Endpoints

Base path: `/api/flash/auth`

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/auth/register` | ❌ | Register new user |
| POST | `/auth/login` | ❌ | Login user |
| POST | `/auth/refresh` | ❌ | Refresh access token |
| POST | `/auth/logout` | ❌ | Logout user |
| GET | `/auth/me` | ✅ | Get current user info |

## 👤 User Profile Endpoints

Base path: `/api/flash`

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/user-profile` | ✅ | Create user profile |
| GET | `/user-profile/{user_id}` | ✅ | Get user profile (own only) |
| PUT | `/user-profile/{user_id}` | ✅ | Update user profile (own only) |
| DELETE | `/user-profile/{user_id}` | ✅ | Delete user profile (own only) |
| GET | `/user-profiles` | ✅ | List all profiles |

## 🎯 Flash AI Endpoints

Base path: `/api/flash`

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/health` | ❌ | Health check |
| GET | `/protected-test` | ✅ | Test authentication |
| POST | `/analyze-job` | 🔓 | Analyze job (optional auth) |
| POST | `/tailor-resume` | 🔓 | Tailor resume |
| POST | `/answer-question` | 🔓 | Answer single question |
| POST | `/fill-application` | 🔓 | Fill entire application |
| POST | `/fill-application-form` | 🔓 | Fill form fields |
| POST | `/approve-application` | 🔓 | Approve & submit |
| GET | `/applications/{user_id}` | ✅ | Get application history |

Legend:
- ✅ = Authentication required
- ❌ = No authentication
- 🔓 = Optional authentication

## 🔄 Complete Flow Example

```python
import httpx

BASE_URL = "http://localhost:8000/api/flash"

# 1. Register (one service!)
register_response = httpx.post(f"{BASE_URL}/auth/register", json={
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123!"
})

auth_data = register_response.json()["data"]
access_token = auth_data["access_token"]
user_id = auth_data["user"]["id"]

# 2. Create profile (protected)
headers = {"Authorization": f"Bearer {access_token}"}

profile_response = httpx.post(
    f"{BASE_URL}/user-profile",
    json={
        "full_name": "John Doe",
        "email": "john@example.com",
        "location": "San Francisco, CA",
        "skills": ["Python", "FastAPI"],
        "years_of_experience": 5
    },
    headers=headers
)

# 3. Analyze job (optional auth, but tracked if provided)
job_response = httpx.post(
    f"{BASE_URL}/analyze-job",
    json={
        "job_description": {
            "title": "Senior Backend Engineer",
            "company": "Tech Corp",
            "description": "Looking for Python expert...",
            "url": "https://example.com/job"
        }
    },
    headers=headers  # Optional but recommended
)

# 4. Fill application form
form_response = httpx.post(
    f"{BASE_URL}/fill-application-form",
    json={
        "form_fields": [
            {
                "field_id": "email",
                "field_name": "email",
                "field_type": "email",
                "label": "Email Address",
                "required": True
            }
        ],
        "user_id": user_id,
        "job_id": "job_123"
    },
    headers=headers
)

print("✅ All done in one service!")
```

## 🔑 Authentication Header Format

For all protected endpoints:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📊 Response Formats

### Authentication Response
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123abc",
      "name": "John Doe",
      "email": "john@example.com"
    },
    "access_token": "eyJhbGci...",
    "refresh_token": "abc123...",
    "expires_at": "2026-02-12T10:30:00Z"
  }
}
```

### Error Response
```json
{
  "detail": "Error message here"
}
```

Common HTTP Status Codes:
- `200` - Success
- `400` - Bad request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (accessing others' resources)
- `404` - Not found
- `500` - Internal server error

## 🎯 Benefits of Consolidated Service

✅ **Single Port** - No need to manage multiple ports  
✅ **Simpler Deployment** - One service to deploy  
✅ **Easier Development** - Start one server, test everything  
✅ **Shared State** - Auth and profiles in same process  
✅ **Less Complexity** - No cross-service communication needed  

## 🚀 Testing

```bash
# Start server
uvicorn app.main:app --reload --port 8000

# Test health
curl http://localhost:8000/api/flash/health

# Register user
curl -X POST http://localhost:8000/api/flash/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "test123456"
  }'

# Copy the access_token from response, then:

# Create profile (use token)
curl -X POST http://localhost:8000/api/flash/user-profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "location": "New York",
    "skills": ["Python"]
  }'
```

## 📝 Migration Notes

If you were using the separate auth service:

**Old:**
- Auth: `http://localhost:8000/api/auth/*`
- Flash: `http://localhost:8000/api/flash/*`

**New:**
- Auth: `http://localhost:8000/api/flash/auth/*` ← Just add `/flash` prefix
- Flash: `http://localhost:8000/api/flash/*` ← Same as before

**Simple migration:**
- Replace `/api/auth/` with `/api/flash/auth/`
- Everything else stays the same!
