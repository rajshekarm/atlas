# Atlas

Atlas is a personal backend platform built with FastAPI.

It serves as a single, modular backend for multiple projects including:
- **Blog Service** - Content management and publishing
- **Flash Service** - AI Job Application Assistant (resume tailoring, auto-fill forms)
- **AI Tools & Agents** - LLM-powered workflows
- **Experiments** - Prototypes and isolated ideas

Rather than creating a separate backend for every project, Atlas provides a shared foundation with clear service boundaries and room to grow.

---


## Project Structure

```
app/
├── main.py                  # Application entry point
├── core/                    # Shared configuration and utilities
│   ├── config.py
│   └── logging.py
└── services/
    ├── blogs/               # Blog service (content, metadata)
    │   ├── router.py
    │   ├── schemas.py
    │   └── store.py
    ├── flash/               # AI Job Application Assistant ⭐ NEW
    │   ├── router.py        # 9 API endpoints
    │   ├── models.py        # 40+ Pydantic models
    │   ├── agents.py        # Agent orchestrator
    │   ├── config.py        # Configuration
    │   ├── services/        # Core business logic
    │   │   ├── job_analyzer.py
    │   │   ├── resume_tailor.py
    │   │   ├── qa_engine.py
    │   │   └── guardrails.py
    │   ├── agents/          # LLM agents
    │   │   ├── resume_agent.py
    │   │   └── qa_agent.py
    │   ├── tests/
    │   ├── README.md
    │   └── TODO.md          # Database implementation checklist
    └── experiments/         # Prototypes and isolated ideas
```

Each service is isolated and owns its own domain logic.

-----------------------

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload
```

API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Services
- **Blogs**: `http://localhost:8000/api/blogs`
- **Flash**: `http://localhost:8000/api/flash` (AI Job Application Assistant)
- **Experiments**: `http://localhost:8000/api/experiments`



---

## Services

### 1. Blog Service
Simple content management for blog posts.

**Endpoints**:
- `GET /api/blogs` - List all blogs
- `GET /api/blogs/{slug}` - Get single blog
- `POST /api/blogs` - Create new blog

**Storage**: JSON file (`data/blogs.json`)

---

### 2. Flash Service - AI Job Application Assistant 🤖

AI-powered assistant that helps users tailor resumes and automatically fill job applications.

**Key Features**:
- Resume tailoring based on job descriptions (ethical guardrails)
- RAG-based question answering for application forms
- Chrome Extension integration for browser automation
- Human-in-the-loop review before submission
- Confidence scoring & validation

**Endpoints**:
- `POST /api/flash/analyze-job` - Analyze job description
- `POST /api/flash/tailor-resume` - Tailor resume for job
- `POST /api/flash/answer-question` - Answer single question
- `POST /api/flash/fill-application` - Fill entire application
- `POST /api/flash/approve-application` - Approve & submit
- `GET /api/flash/profile/{user_id}` - Get user profile
- `POST /api/flash/profile` - Create/update profile
- `GET /api/flash/applications/{user_id}` - Application history

**⚠️ Database Required**: Flash service needs persistent storage (see [TODO.md](app/services/flash/TODO.md))
- User profiles
- Application history & logs
- Vector store for RAG (past answers, resume embeddings)

**Documentation**: [Flash README](app/services/flash/README.md)

---

### 3. Experiments Service
Prototypes and isolated experimental features.


---

## Design Philosophy

- **One backend, many services** - Centralized platform for all projects
- **Clear boundaries over premature microservices** - Services own their domains
- **Simple persistence first, scalable later** - Start with files/SQLite, migrate when needed
- **Optimize for learning, iteration, and clarity** - Developer experience matters
- **AI-first architecture** - Built to support LLMs, agents, and vector search

---

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Models**: Pydantic v2
- **AI/LLM**: Azure OpenAI
- **Storage**: 
  - JSON files (blogs - temporary)
  - SQLite/PostgreSQL (planned for Flash service)
  - FAISS/pgvector (planned for vector embeddings)
- **Deployment**: Azure (planned)

---

## Database Status

### Current State
- **Blogs**: JSON file storage (`data/blogs.json`)
- **Flash**: ⚠️ **Placeholders only** - requires database implementation

### Planned Implementation
Flash service requires:
1. **Relational DB** (SQLite → PostgreSQL)
   - User profiles
   - Application history
   - Job analyses
   
2. **Vector Store** (FAISS → pgvector)
   - RAG for question answering
   - Semantic search over past answers
   - Resume embeddings

See [Flash TODO](app/services/flash/TODO.md) for complete implementation plan.
---

## AI & ML Capabilities

Atlas supports AI and agent-based workloads without requiring structural changes.

### Current Integrations
- **Azure OpenAI** - GPT models for text generation
- **Pydantic AI** - Type-safe AI model interactions
- **LangChain** - Tool-augmented LLM workflows (planned)
- **FAISS/pgvector** - Vector search for RAG (planned)

### Flash Service AI Features
- **Job Analysis Agent** - Extracts skills, requirements from job descriptions
- **Resume Tailoring Agent** - Ethically rewrites resumes with guardrails
- **Q&A Engine** - RAG-based question answering using user profile + past answers
- **Guardrails Service** - Validates AI outputs for truthfulness and safety

### Architecture
```
services/
└── flash/
    ├── agents/
    │   ├── resume_agent.py      # Resume analysis
    │   └── qa_agent.py           # Question answering
    ├── services/
    │   ├── job_analyzer.py       # Job description parsing
    │   ├── resume_tailor.py      # Resume customization
    │   ├── qa_engine.py          # RAG-powered Q&A
    │   └── guardrails.py         # Safety & validation
    └── router.py                 # API endpoints
```

---

## Environment Setup

Create a `.env` file in the root directory:

```bash
# Azure OpenAI (for Flash service)
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Database (when implemented)
DATABASE_URL=sqlite:///./data/flash/flash.db
# Or for production: postgresql://user:pass@localhost/atlas

# Vector Store (when implemented)
VECTOR_STORE_TYPE=faiss  # or pgvector
```

---

## Development Roadmap

### ✅ Completed
- FastAPI backend foundation
- Blog service (JSON storage)
- Flash service core logic (9 endpoints, 4 services, 2 agents)
- AI agent architecture
- Guardrails & validation

### 🚧 In Progress
- Database implementation for Flash service
- Vector store integration (RAG)

### 📋 Planned
- User authentication & authorization
- Chrome Extension for Flash service
- PostgreSQL migration
- Azure deployment
- Rate limiting & API keys
- Background job processing (Celery)

---

## Quick Reference

### Architecture Diagram
```
Chrome Extension → FastAPI Backend → Azure OpenAI
                         ↓
                   [Services Layer]
                         ↓
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Blogs          Flash       Experiments
          ↓              ↓
    blogs.json    [DB + Vector Store]
                  (needs implementation)
```

### Service Comparison

| Feature | Blogs | Flash | Experiments |
|---------|-------|-------|-------------|
| Status | ✅ Production | ⚠️ Needs DB | 🚧 Prototype |
| Storage | JSON file | Placeholders | N/A |
| AI/LLM | No | Yes (Azure OpenAI) | Varies |
| Endpoints | 3 | 9 | TBD |
| Documentation | Basic | [Detailed](app/services/flash/README.md) | N/A |

---

## Contributing

This is a personal backend platform, but the architecture and patterns may be useful for reference.

### Key Design Patterns
- Service-based architecture (not microservices)
- Pydantic for type safety and validation
- Separation of routing, business logic, and data access
- AI agents as composable services
- Guardrails for AI safety

---

## License

Personal project - not currently licensed for external use.

---

## Contact

For questions or collaboration: [Your contact info]
