# 🔐 Cross-Service Authentication

How Flash (and other services) verify authentication from the Auth service.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Atlas Platform                          │
├──────────────────┬──────────────────────┬───────────────────┤
│   Auth Service   │   Flash Service      │   Other Services  │
│   /api/auth      │   /api/flash         │   /api/...        │
├──────────────────┴──────────────────────┴───────────────────┤
│              app.core.auth (Shared Auth Utils)              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Dependencies:                                       │    │
│  │  - get_current_user_id()    ✅ Required auth       │    │
│  │  - get_optional_user_id()   🔓 Optional auth       │    │
│  │  - get_current_user()       ✅ Full user info      │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. User Authenticates with Auth Service
```bash
POST /api/auth/login
Body: {"email": "user@example.com", "password": "pass123"}

Response:
{
  "success": true,
  "data": {
    "user": { "id": "user_123", ... },
    "access_token": "eyJhbGci...",  # ← JWT token
    "refresh_token": "...",
    "expires_at": "2026-02-12T10:30:00Z"
  }
}
```

### 2. Client Stores Token
Frontend stores `access_token` and includes it in subsequent requests.

### 3. Flash Service Verifies Token
When client calls Flash endpoints with token, Flash uses shared auth utils:

```python
# In Flash router.py
from app.core.auth import get_current_user_id

@router.post("/user-profile")
async def create_profile(
    request: CreateProfileRequest,
    user_id: str = Depends(get_current_user_id)  # ← Verifies JWT
):
    # user_id is extracted and verified from token
    # If invalid, FastAPI returns 401 automatically
    return {"message": f"Profile created for {user_id}"}
```

## Usage Examples

### Protected Endpoint (Authentication Required)

```python
from fastapi import Depends
from app.core.auth import get_current_user_id

@router.post("/protected-endpoint")
async def protected(user_id: str = Depends(get_current_user_id)):
    """Requires valid JWT token in Authorization header"""
    return {"user_id": user_id}
```

**Client Request:**
```bash
POST /api/flash/protected-endpoint
Headers:
  Authorization: Bearer eyJhbGci...
  Content-Type: application/json
```

**Responses:**
- ✅ `200` - Token valid, returns data
- ❌ `401` - Token missing or invalid

---

### Optional Authentication

```python
from app.core.auth import get_optional_user_id

@router.get("/analyze-job")
async def analyze_job(
    request: AnalyzeJobRequest,
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """Works with or without authentication"""
    if user_id:
        # Track analytics for authenticated user
        logger.info(f"Job analyzed by user: {user_id}")
    
    return analyze_result
```

---

### Get Full User Info

```python
from app.core.auth import get_current_user

@router.get("/my-profile")
async def get_my_profile(user: dict = Depends(get_current_user)):
    """Returns both user_id and email"""
    return {
        "user_id": user["user_id"],
        "email": user["email"]
    }
```

## Protected Flash Endpoints

Currently protected (require authentication):

### User Profile Management
- ✅ `POST /api/flash/user-profile` - Create profile (uses authenticated user_id)
- ✅ `GET /api/flash/user-profile/{user_id}` - Get profile (own profile only)
- ✅ `PUT /api/flash/user-profile/{user_id}` - Update profile (own profile only)
- ✅ `DELETE /api/flash/user-profile/{user_id}` - Delete profile (own profile only)

### Public Endpoints (No auth required)
- 🔓 `GET /api/flash/health` - Health check
- 🔓 `POST /api/flash/analyze-job` - Job analysis (optional auth for tracking)
- 🔓 `POST /api/flash/fill-application-form` - Fill forms (optional auth)

### Example Protected Endpoint
- ✅ `GET /api/flash/protected-test` - Test authentication (demo)

## Security Features

### 1. **Token Verification**
- JWT signature validation
- Expiration check (1 hour for access tokens)
- Payload validation (user_id, email)

### 2. **User Isolation**
Users can only access/modify their own resources:
```python
# Automatic check in endpoints
if user_id != authenticated_user_id:
    raise HTTPException(403, "You can only access your own profile")
```

### 3. **Automatic Error Handling**
FastAPI automatically returns proper HTTP errors:
- `401 Unauthorized` - Token missing/invalid/expired
- `403 Forbidden` - User trying to access others' resources

## Testing

### 1. Register & Login
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"test123456"}'

# Response includes access_token
```

### 2. Use Token in Flash Service
```bash
# Create profile (protected)
curl -X POST http://localhost:8000/api/flash/user-profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "location": "New York",
    "skills": ["Python", "FastAPI"]
  }'
```

### 3. Test Protected Endpoint
```bash
# Should work with valid token
curl -X GET http://localhost:8000/api/flash/protected-test \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# Should return 401 without token
curl -X GET http://localhost:8000/api/flash/protected-test
```

## Implementation Details

### Token Payload Structure
```json
{
  "user_id": "user_123",
  "email": "user@example.com",
  "exp": 1707738600,        // Expiration timestamp
  "iat": 1707735000,        // Issued at timestamp
  "type": "access"          // Token type
}
```

### Shared Auth Module Location
```
app/
  core/
    auth.py              ← Shared authentication dependencies
  services/
    auth/
      router.py          ← Issues tokens
      utils.py           ← Verifies tokens
    flash/
      router.py          ← Uses auth dependencies
```

## Adding Auth to New Endpoints

To protect any endpoint in any service:

```python
# Step 1: Import dependency
from fastapi import Depends
from app.core.auth import get_current_user_id

# Step 2: Add to endpoint
@router.post("/my-endpoint")
async def my_endpoint(
    request: MyRequest,
    user_id: str = Depends(get_current_user_id)  # ← Add this
):
    # user_id is now available and verified
    return {"message": f"Hello {user_id}"}
```

## Future Enhancements

- [ ] Role-based access control (RBAC)
- [ ] Permission system (read/write permissions)
- [ ] API rate limiting per user
- [ ] Admin endpoints with super-user check
- [ ] Audit logging for protected operations
- [ ] Token refresh automation in client
