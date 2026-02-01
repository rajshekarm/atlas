# Flash - AI Job Application Assistant 🤖

## Overview
AI-powered assistant that helps users tailor resumes and automatically fill job applications using a Chrome Extension + FastAPI backend.

## Key Features
✅ Resume tailoring based on Job Description (safe & ethical)  
✅ RAG-based question answering for application forms  
✅ Chrome Extension for real-browser automation  
✅ Human-in-the-loop review before submission  
✅ Confidence scoring & guardrails  

## Architecture

```
Chrome Extension → FastAPI Backend → LLM + Vector DB
```

### Tech Stack
- **Backend**: FastAPI (Python)
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

### Job Analysis
- `POST /api/flash/analyze-job` - Analyze job description

### Resume Tailoring
- `POST /api/flash/tailor-resume` - Tailor resume for job

### Question Answering
- `POST /api/flash/answer-question` - Answer single question
- `POST /api/flash/fill-application` - Fill entire application

### Submission
- `POST /api/flash/approve-application` - Approve & submit

### User Management
- `GET /api/flash/profile/{user_id}` - Get user profile
- `POST /api/flash/profile` - Create/update profile
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

### 3. Run Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Test Endpoints
```bash
curl http://localhost:8000/api/flash/health
```

## Usage Example

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
