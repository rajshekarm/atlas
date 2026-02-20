# Flash API Documentation

## Base URL
```
http://localhost:8000/api/flash
```

---

## Authentication
Currently, no authentication is implemented. In production, add JWT/OAuth2 authentication.

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if Flash service is running.

**Response:**
```json
{
  "status": "ok",
  "service": "flash"
}
```

---

### 2. Analyze Job Description

**POST** `/analyze-job`

Analyzes a job description and extracts key requirements, skills, and metadata.

**Request Body:**
```json
{
  "job_description": {
    "title": "Senior Backend Engineer",
    "company": "Tech Corp",
    "location": "San Francisco, CA",
    "description": "Full job description text...",
    "requirements": [
      "5+ years of Python experience",
      "Experience with FastAPI"
    ],
    "responsibilities": [
      "Design and implement backend services",
      "Lead technical discussions"
    ],
    "preferred_qualifications": [
      "AWS experience",
      "Kubernetes knowledge"
    ],
    "url": "https://example.com/job/12345"
  },
  "user_profile_id": "user123"  // Optional
}
```

**Response:**
```json
{
  "job_id": "a1b2c3d4e5f6g7h8",
  "required_skills": ["python", "fastapi", "rest api"],
  "preferred_skills": ["aws", "kubernetes"],
  "technologies": ["python", "fastapi", "postgresql", "docker"],
  "seniority_level": "senior",
  "role_focus": "backend",
  "key_requirements": [
    "5+ years of Python experience",
    "Experience with FastAPI"
  ],
  "match_score": null,
  "timestamp": "2026-02-01T10:30:00"
}
```

---

### 3. Tailor Resume

**POST** `/tailor-resume`

Tailors a master resume to match a specific job description with ethical guardrails.

**Request Body:**
```json
{
  "job_id": "a1b2c3d4e5f6g7h8",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "job_id": "a1b2c3d4e5f6g7h8",
  "original_resume_path": "./data/resumes/master_resume.txt",
  "tailored_resume_path": "./data/resumes/resume_tailored_a1b2c3_20260201_103000.txt",
  "sections": [
    {
      "section_type": "summary",
      "original_content": "Original summary text...",
      "tailored_content": "Enhanced summary emphasizing relevant skills...",
      "changes": ["Emphasized Python experience", "Added API development focus"]
    }
  ],
  "changes_summary": "Made 5 improvements to better match job requirements",
  "confidence": "high",
  "requires_approval": true,
  "timestamp": "2026-02-01T10:30:00"
}
```

---

### 4. Answer Single Question

**POST** `/answer-question`

Answers a single application question using RAG (Retrieval-Augmented Generation).

**Request Body:**
```json
{
  "question_context": {
    "question": "Why do you want to work at our company?",
    "field_id": "motivation_question",
    "field_type": "textarea",
    "job_id": "a1b2c3d4e5f6g7h8",
    "resume_path": "./data/resumes/master_resume.txt",
    "user_profile": null
  },
  "user_id": "user123"
}
```

**Response:**
```json
{
  "field_id": "motivation_question",
  "question": "Why do you want to work at our company?",
  "answer": "I'm excited about this opportunity because...",
  "confidence": "high",
  "confidence_score": 0.85,
  "sources": [
    {
      "source_type": "profile",
      "content": "Passionate about backend systems...",
      "relevance_score": 0.9
    }
  ],
  "requires_review": false,
  "alternative_answers": [
    "Alternative phrasing 1...",
    "Alternative phrasing 2..."
  ],
  "timestamp": "2026-02-01T10:30:00"
}
```

---

### 5. Fill Complete Application

**POST** `/fill-application`

Fills an entire application form with AI-generated answers.

**Request Body:**
```json
{
  "application_form": {
    "form_id": "form123",
    "url": "https://example.com/apply",
    "job_id": "a1b2c3d4e5f6g7h8",
    "fields": [
      {
        "field_id": "email",
        "field_name": "email_address",
        "field_type": "email",
        "label": "Email Address",
        "placeholder": "your@email.com",
        "required": true,
        "options": null,
        "validation_rules": null
      },
      {
        "field_id": "experience",
        "field_name": "years_experience",
        "field_type": "dropdown",
        "label": "Years of Experience",
        "required": true,
        "options": ["0-2", "3-5", "6-10", "10+"]
      }
    ],
    "steps": ["Personal Info", "Experience", "Questions"],
    "current_step": 0
  },
  "job_description": {
    "title": "Senior Backend Engineer",
    "company": "Tech Corp",
    "description": "Job description...",
    "url": "https://example.com/job"
  },
  "user_id": "user123",
  "auto_submit": false
}
```

**Response:**
```json
{
  "application_id": "app_a1b2c3_user123",
  "job_id": "a1b2c3d4e5f6g7h8",
  "company": "Tech Corp",
  "role": "Senior Backend Engineer",
  "filled_fields": [
    {
      "field_id": "email",
      "field_name": "email_address",
      "answer": "john.doe@email.com",
      "confidence": "high",
      "source": "profile"
    },
    {
      "field_id": "experience",
      "field_name": "years_experience",
      "answer": "6-10",
      "confidence": "high",
      "source": "profile"
    }
  ],
  "resume_path": "./data/resumes/master_resume.txt",
  "status": "review_required",
  "ready_for_submission": true,
  "warnings": null,
  "timestamp": "2026-02-01T10:30:00"
}
```

**Flow Diagram (Mermaid):**
- `app/services/flash/docs/fill_application_form_flow.mmd`

---

### 6. Approve & Submit Application

**POST** `/approve-application`

Approves a filled application and prepares it for submission.

**Request Body:**
```json
{
  "application_id": "app_a1b2c3_user123",
  "user_id": "user123",
  "edited_fields": [
    {
      "field_id": "experience",
      "field_name": "years_experience",
      "answer": "10+",  // User edited this
      "confidence": "high",
      "source": "user_edited"
    }
  ]
}
```

**Response:**
```json
{
  "application_id": "app_a1b2c3_user123",
  "success": true,
  "submitted_at": "2026-02-01T10:35:00",
  "error_message": null,
  "confirmation_number": null  // Filled by Chrome Extension after submission
}
```

---

### 7. Get User Profile

**GET** `/profile/{user_id}`

Retrieves user profile information.

**Response:**
```json
{
  "user_id": "user123",
  "full_name": "John Doe",
  "email": "john.doe@email.com",
  "phone": "+1-555-0123",
  "location": "San Francisco, CA",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "github_url": "https://github.com/johndoe",
  "portfolio_url": "https://johndoe.com",
  "current_title": "Senior Software Engineer",
  "years_of_experience": 5,
  "skills": ["Python", "FastAPI", "PostgreSQL"],
  "preferred_roles": ["Backend Engineer", "Full Stack Engineer"],
  "work_authorization": "US Citizen",
  "master_resume_path": "./data/resumes/master_resume.txt",
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-02-01T10:00:00"
}
```

---

### 8. Create/Update User Profile

**POST** `/profile`

Creates or updates a user profile.

**Request Body:**
```json
{
  "user_id": "user123",
  "full_name": "John Doe",
  "email": "john.doe@email.com",
  "phone": "+1-555-0123",
  "location": "San Francisco, CA",
  "current_title": "Senior Software Engineer",
  "years_of_experience": 5,
  "skills": ["Python", "FastAPI"],
  "preferred_roles": ["Backend Engineer"],
  "work_authorization": "US Citizen",
  "master_resume_path": "./data/resumes/master_resume.txt"
}
```

**Response:** Same as GET profile response

---

### 9. Get Application History

**GET** `/applications/{user_id}`

Retrieves user's past applications.

**Response:**
```json
[
  {
    "application_id": "app_123",
    "user_id": "user123",
    "job_id": "job456",
    "company": "Tech Corp",
    "role": "Backend Engineer",
    "resume_version": "resume_tailored_abc123.txt",
    "answers_count": 15,
    "status": "submitted",
    "submitted_at": "2026-01-15T14:30:00",
    "created_at": "2026-01-15T14:00:00"
  }
]
```

---

## Error Responses

All endpoints may return error responses in this format:

```json
{
  "error": "ValidationError",
  "message": "Detailed error message",
  "details": {
    "field": "additional context"
  },
  "timestamp": "2026-02-01T10:30:00"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Not Found
- `500` - Internal Server Error

---

## Rate Limiting

Currently not implemented. Add rate limiting in production.

---

## Data Models

### Field Types
- `text` - Single-line text input
- `textarea` - Multi-line text input
- `dropdown` - Dropdown select
- `radio` - Radio button selection
- `checkbox` - Checkbox
- `file` - File upload
- `email` - Email input
- `phone` - Phone number input
- `date` - Date picker

### Confidence Levels
- `high` - Confidence score >= 0.8
- `medium` - Confidence score >= 0.5
- `low` - Confidence score < 0.5

### Application Status
- `pending` - Application created
- `in_progress` - Being filled
- `review_required` - Ready for user review
- `approved` - User approved
- `submitted` - Successfully submitted
- `failed` - Submission failed

---

## Best Practices

1. **Always review low-confidence answers** before submission
2. **Use the tailor-resume endpoint** before applying to match job requirements
3. **Store user profiles** to speed up future applications
4. **Enable guardrails** to ensure ethical AI usage
5. **Test in development** before production use

---

## Integration Example (Python)

```python
import httpx

class FlashClient:
    def __init__(self, base_url="http://localhost:8000/api/flash"):
        self.base_url = base_url
        self.client = httpx.Client()
    
    def analyze_job(self, job_description):
        response = self.client.post(
            f"{self.base_url}/analyze-job",
            json={"job_description": job_description}
        )
        return response.json()
    
    def answer_question(self, question_context, user_id):
        response = self.client.post(
            f"{self.base_url}/answer-question",
            json={
                "question_context": question_context,
                "user_id": user_id
            }
        )
        return response.json()

# Usage
client = FlashClient()
analysis = client.analyze_job({
    "title": "Backend Engineer",
    "company": "Tech Corp",
    "description": "...",
    "url": "https://example.com/job"
})
```

---

## WebSocket Support (Future)

Real-time updates for long-running operations will be added in future versions.

---

For more details, visit the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
