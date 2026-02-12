# Flash - AI Job Application Assistant 🤖

## Overview
**All-in-one service** combining AI-powered job application assistance with user authentication.

AI-powered assistant that helps users tailor resumes and automatically fill job applications using a Chrome Extension + FastAPI backend.

## Key Features
✅ **Built-in Authentication** - JWT-based auth, no separate service needed  
✅ Resume tailoring based on Job Description (safe & ethical)  
✅ RAG-based question answering for application forms  
✅ Chrome Extension for real-browser automation  
✅ Human-in-the-loop review before submission  
✅ Confidence scoring & guardrails  

## Architecture

```
Chrome Extension → Flash Service (All-in-One)
                      ├── Authentication
                      ├── Job Analysis
                      ├── Resume Tailoring
                      ├── Form Filling
                      └── User Profiles
                           ↓
                   LLM + Vector DB
```

### Tech Stack
- **Backend**: FastAPI (Python)
- **Authentication**: JWT + bcrypt
- **AI**: Azure OpenAI
- **Vector DB**: Azure AI Search / Chroma
- **Storage**: Azure Blob Storage / Local
- **Frontend**: Chrome Extension (JS + React)

## Project Structure

```
flash/
├── models.py              # Pydantic models for all API schemas
├── router.py              # FastAPI endpoints
├── agents.py              # Agent orchestrator
├── services/              # Core business logic
│   ├── job_analyzer.py    # Job description analysis
│   ├── resume_tailor.py   # Resume tailoring with guardrails
│   ├── qa_engine.py       # RAG-based question answering
│   └── guardrails.py      # Ethical validation & safety checks
└── agents/                # LLM-powered agents
    ├── resume_agent.py    # Resume analysis agent
    └── qa_agent.py        # Question answering agent
```

## API Endpoints

### 🔐 Authentication (No separate service needed!)
- `POST /api/flash/auth/register` - Register new user
- `POST /api/flash/auth/login` - Login user
- `POST /api/flash/auth/refresh` - Refresh access token
- `POST /api/flash/auth/logout` - Logout user
- `GET /api/flash/auth/me` - Get current user info (requires auth)

### 📊 Job Analysis
- `POST /api/flash/analyze-job` - Analyze job description

### 📄 Resume Tailoring
- `POST /api/flash/tailor-resume` - Tailor resume for job

### ❓ Question Answering
- `POST /api/flash/answer-question` - Answer single question
- `POST /api/flash/fill-application` - Fill entire application
- `POST /api/flash/fill-application-form` - Fill form fields with optional user profile

### ✅ Submission
- `POST /api/flash/approve-application` - Approve & submit

### 👤 User Profile Management (Protected - requires auth)
- `POST /api/flash/user-profile` - Create new user profile
- `GET /api/flash/user-profile/{user_id}` - Get user profile by ID
- `PUT /api/flash/user-profile/{user_id}` - Update user profile
- `DELETE /api/flash/user-profile/{user_id}` - Delete user profile
- `GET /api/flash/user-profiles` - List all user profiles

### 📋 Application History
- `GET /api/flash/applications/{user_id}` - Application history

## Core Modules

### 1. Job Analyzer (`job_analyzer.py`)
- Extracts required/preferred skills
- Identifies technologies
- Determines seniority level
- Analyzes role focus

### 2. Resume Tailor (`resume_tailor.py`)
- Ethically tailors resumes to match job descriptions
- **Strict Guardrails**:
  - ❌ No new skills added
  - ❌ No date changes
  - ❌ No fake experience
  - ✅ Only rephrase existing content

### 3. QA Engine (`qa_engine.py`)
- RAG-powered question answering
- Retrieves context from:
  - User profile
  - Resume
  - Past approved answers (vector DB)
- Generates answers with confidence scores

### 4. Guardrails (`guardrails.py`)
- Validates resume changes
- Checks answer truthfulness
- Ensures ethical operation
- Blocks prohibited content

## Ethical Design Principles

🛡️ **No CAPTCHA bypass**  
🛡️ **No fake experience**  
🛡️ **User approval required before submission**  
🛡️ **Confidence scoring for transparency**  
🛡️ **Guardrails on all AI-generated content**  

## How It Works (End-to-End)

### 1. User Initiates
- User navigates to job application page
- Clicks Chrome Extension → "Apply with AI"

### 2. Job Analysis
- Extension extracts job description + form fields
- Backend analyzes job requirements

### 3. Resume Tailoring
- System compares master resume with job requirements
- AI rewrites sections to emphasize relevant skills
- **Guardrails** ensure no fake experience
- User reviews & approves changes

### 4. Question Answering (RAG)
- For each form field, system retrieves relevant context
- AI generates truthful answer
- Confidence score indicates reliability

### 5. Form Filling
- Chrome Extension auto-fills fields
- Handles text, dropdowns, radio buttons, file uploads
- Navigates multi-step forms

### 6. Human Review
- All answers highlighted for review
- User can edit, approve, or cancel
- Final validation before submission

### 7. Submission & Learning
- Application submitted (via Chrome Extension)
- System logs approved answers
- Future applications become faster & more accurate

## Setup

### 1. Environment Variables
Create `.env` file:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=flash-knowledge-base

# Azure Blob Storage (optional)
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_STORAGE_CONTAINER_NAME=resumes
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Server (Single Service!)
```bash
uvicorn app.main:app --reload --port 8000
```

**That's it!** One command starts everything:
- ✅ Authentication service
- ✅ Flash AI service  
- ✅ User profile management
- ✅ All features ready to use

### 4. Test Endpoints
```bash
# Test health
curl http://localhost:8000/api/flash/health

# Test auth
curl -X POST http://localhost:8000/api/flash/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"test123456"}'
```

## Usage Example

### 1. Register & Login (All in Flash!)
```python
import httpx

# Register new user
response = httpx.post("http://localhost:8000/api/flash/auth/register", json={
    "name": "Jane Smith",
    "email": "jane@example.com",
    "password": "SecurePass123!"
})

data = response.json()
access_token = data["data"]["access_token"]
refresh_token = data["data"]["refresh_token"]
user_id = data["data"]["user"]["id"]

print(f"✅ Registered! User ID: {user_id}")
print(f"🔑 Access Token: {access_token[:20]}...")
```

### 2. Create User Profile (Protected)
```python
# Use the access token from registration
headers = {"Authorization": f"Bearer {access_token}"}

profile_data = {
    "full_name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+1-555-0199",
    "location": "New York, NY",
    "current_title": "Senior Software Engineer",
    "years_of_experience": 7,
    "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
    "preferred_roles": ["Backend Engineer", "Full Stack Engineer"],
    "work_authorization": "US Citizen",
    "visa_status": "N/A",
    "notice_period": "2 weeks",
    "salary_expectation": "$150k - $180k"
}

response = httpx.post(
    "http://localhost:8000/api/flash/user-profile",
    json=profile_data,
    headers=headers  # ← Use authenticated headers
)
user_profile = response.json()
print(f"✅ Profile created for user {user_id}")
```

### 3. Update User Profile
    "current_title": "Senior Software Engineer",
    "years_of_experience": 7,
    "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
    "preferred_roles": ["Backend Engineer", "Full Stack Engineer"],
    "work_authorization": "US Citizen",
    "visa_status": "N/A",
    "notice_period": "2 weeks",
    "salary_expectation": "$150k - $180k"
}

response = httpx.post("http://localhost:8000/api/flash/user-profile", json=profile_data)
user_profile = response.json()
user_id = user_profile["user_id"]
```

### Update User Profile
```python
update_data = {
    "location": "Boston, MA",
    "salary_expectation": "$160k - $190k",
    "skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"]
}

response = httpx.put(f"http://localhost:8000/api/flash/user-profile/{user_id}", json=update_data)
updated_profile = response.json()
```

### Analyze Job
```python
import httpx

job_data = {
    "job_description": {
        "title": "Senior Backend Engineer",
        "company": "Tech Corp",
        "description": "We're looking for...",
        "requirements": ["5+ years Python", "FastAPI", "PostgreSQL"],
        "url": "https://example.com/job"
    }
}

response = httpx.post("http://localhost:8000/api/flash/analyze-job", json=job_data)
analysis = response.json()
```

### Fill Application Form
```python
fill_data = {
    "form_fields": [
        {
            "field_id": "email",
            "field_name": "email",
            "field_type": "email",
            "label": "Email Address",
            "required": True
        },
        {
            "field_id": "experience",
            "field_name": "experience",
            "field_type": "textarea",
            "label": "Tell us about your experience",
            "required": True
        }
    ],
    "user_id": user_id,
    "job_id": "job123",
    "user_profile": {
        "email": "jane@example.com",
        "years_of_experience": 7,
        "current_title": "Senior Software Engineer"
    }
}

response = httpx.post("http://localhost:8000/api/flash/fill-application-form", json=fill_data)
answers = response.json()
```

### Answer Question
```python
import httpx

job_data = {
    "job_description": {
        "title": "Senior Backend Engineer",
        "company": "Tech Corp",
        "description": "We're looking for...",
        "requirements": ["5+ years Python", "FastAPI", "PostgreSQL"],
        "url": "https://example.com/job"
    }
}

response = httpx.post("http://localhost:8000/api/flash/analyze-job", json=job_data)
analysis = response.json()
```

### Answer Question
```python
question_data = {
    "question_context": {
        "question": "Why do you want to work here?",
        "field_id": "motivation",
        "field_type": "textarea",
        "job_id": "job123"
    },
    "user_id": "user456"
}

response = httpx.post("http://localhost:8000/api/flash/answer-question", json=question_data)
answer = response.json()
```

## Future Enhancements

- 📊 Multi-resume profiles
- 📈 Analytics dashboard
- 🎯 ATS score estimation
- 🔄 Application tracking
- 🤖 Interview preparation assistant
- 📧 Follow-up email generator

## Disclaimer

This tool assists users in applying to jobs they are **legally authorized** to apply for. It does not:
- Bypass security measures (CAPTCHA)
- Fabricate experience or credentials
- Submit applications without user approval
- Violate terms of service of job platforms

## Contributing

This is a personal project as part of the Atlas multi-service platform.

## License

Private project - All rights reserved
