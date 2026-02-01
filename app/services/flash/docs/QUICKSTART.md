# Flash Service - Quick Start Guide

## 🚀 Getting Started

### 1. Install Dependencies

```bash
# From the project root (atlas/)
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.flash.example .env
```

Edit `.env` and add your Azure credentials:

```bash
# Minimum required for basic functionality
FLASH_AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
FLASH_AZURE_OPENAI_API_KEY=your-api-key
```

### 3. Create Data Directories

```bash
mkdir -p data/flash
mkdir -p data/resumes
mkdir -p data/knowledge_base
```

### 4. Run the Server

```bash
# From project root
uvicorn app.main:app --reload --port 8000
```

Server will be available at: `http://localhost:8000`

### 5. Verify Setup

Open your browser: `http://localhost:8000/docs`

You should see the FastAPI interactive documentation with Flash endpoints.

Test the health endpoint:
```bash
curl http://localhost:8000/api/flash/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "flash"
}
```

---

## 🧪 Testing

Run the test suite:

```bash
pytest app/services/flash/tests/test_flash.py -v
```

---

## 📚 API Usage Examples

### 1. Analyze a Job Description

```bash
curl -X POST "http://localhost:8000/api/flash/analyze-job" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": {
      "title": "Senior Backend Engineer",
      "company": "Tech Corp",
      "description": "Looking for experienced Python developer",
      "requirements": ["Python", "FastAPI", "PostgreSQL"],
      "url": "https://example.com/job"
    }
  }'
```

### 2. Get User Profile

```bash
curl http://localhost:8000/api/flash/profile/user123
```

### 3. Answer a Question

```bash
curl -X POST "http://localhost:8000/api/flash/answer-question" \
  -H "Content-Type: application/json" \
  -d '{
    "question_context": {
      "question": "What is your email?",
      "field_id": "email_field",
      "field_type": "email",
      "job_id": "job123"
    },
    "user_id": "user456"
  }'
```

---

## 🏗️ Project Structure

```
flash/
├── README.md              # Main documentation
├── QUICKSTART.md          # This file
├── config.py              # Configuration management
├── models.py              # Pydantic schemas (100+ models)
├── router.py              # API endpoints
├── agents.py              # Agent orchestrator
│
├── services/              # Core business logic
│   ├── job_analyzer.py    # Analyzes job descriptions
│   ├── resume_tailor.py   # Tailors resumes ethically
│   ├── qa_engine.py       # RAG-based QA system
│   └── guardrails.py      # Validation & safety
│
├── agents/                # LLM-powered agents
│   ├── resume_agent.py    # Resume analysis
│   └── qa_agent.py        # Question answering
│
└── tests/                 # Test suite
    └── test_flash.py
```

---

## 🔧 Development Mode

### Enable Debug Logging

Add to your `.env`:
```bash
LOG_LEVEL=DEBUG
```

### Hot Reload

The server automatically reloads when you edit files (when using `--reload`).

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🌐 Integration with Chrome Extension

### CORS Configuration

The backend is already configured to accept requests from Chrome extensions.

See [app/main.py](../../main.py):
```python
allow_origins=[
    "http://localhost:5173",
    "http://localhost:3000",
    "chrome-extension://*"
]
```

### Chrome Extension Setup

1. Your Chrome Extension should make requests to: `http://localhost:8000/api/flash/...`
2. Use the `/analyze-job` endpoint to submit job details
3. Use the `/fill-application` endpoint to get answers for all fields
4. Use the `/approve-application` endpoint before final submission

---

## 📊 Monitoring

### Check Service Health

```bash
curl http://localhost:8000/health           # Overall health
curl http://localhost:8000/api/flash/health # Flash service health
```

### View Logs

Logs are output to console. For production, configure proper logging:

```python
# In config.py or logging setup
import logging
logging.basicConfig(level=logging.INFO)
```

---

## 🛠️ Troubleshooting

### Issue: Module not found errors

**Solution**: Make sure you're in the project root and have installed all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Azure OpenAI not working

**Solution**: The service works in fallback mode without Azure. To use Azure:
1. Verify your credentials in `.env`
2. Check endpoint URL format
3. Ensure your deployment name is correct

### Issue: CORS errors from Chrome Extension

**Solution**: CORS is already configured. If still seeing errors:
1. Check the extension is sending proper headers
2. Verify the request method is allowed
3. Check browser console for detailed error

---

## 🎯 Next Steps

1. **Set up Azure Resources** (optional but recommended):
   - Azure OpenAI for LLM capabilities
   - Azure AI Search for vector storage
   - Azure Blob Storage for resume storage

2. **Build Chrome Extension**:
   - Use the API endpoints provided
   - Implement form field detection
   - Add user approval UI

3. **Customize**:
   - Adjust guardrail settings in `config.py`
   - Modify prompts in service files
   - Add custom validation rules

---

## 📖 Additional Resources

- Main README: [README.md](README.md)
- FastAPI Documentation: https://fastapi.tiangolo.com
- Azure OpenAI: https://learn.microsoft.com/azure/ai-services/openai/

---

## 🆘 Support

For issues or questions:
1. Check the main [README.md](README.md)
2. Review API documentation at `/docs`
3. Check application logs for errors

---

**Happy Coding! 🚀**
