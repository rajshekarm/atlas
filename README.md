# Atlas

Atlas is a personal backend platform built with FastAPI.

It serves as a single, modular backend for multiple projects including:
- Blog content and publishing
- AI-powered tools and agents
- Experiments and prototypes

Rather than creating a separate backend for every project, Atlas provides a shared foundation with clear service boundaries and room to grow.

---


## Project Structure

app/
├── main.py # Application entry point
├── core/ # Shared configuration and utilities
└── services/
├── blogs/ # Blog service (content, metadata)
├── ai/ # AI and agent-based services
└── experiments/ # Prototypes and isolated ideas



Each service is isolated and owns its own domain logic.

-----------------------

## Running Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload


API documentation is available at:

http://localhost:8000/docs



"""
AI service layer.

This module is intended to host:
- Model inference endpoints
- Agent execution loops
- Tool orchestration
- Vector-based retrieval workflows

Implementations will be added incrementally as projects evolve.
"""


Design Philosophy

One backend, many services

Clear boundaries over premature microservices

Simple persistence first, scalable later

Optimize for learning, iteration, and clarity

--------------------------------------------------------------------------

## Tech Stack

- **Python**
- **FastAPI**
- **Pydantic**
- **JSON-based storage (temporary)**
- Azure deployment (planned)

The platform is designed to evolve toward persistent storage and more advanced infrastructure as needed.

-----------------------------------------------------------------------------------------------------
Services
## AI & ML Readiness

Atlas is designed to support AI and agent-based workloads without requiring structural changes to the backend.

Planned integrations include:
- PyTorch for model inference and experimentation
- Hugging Face Transformers for NLP and multimodal models
- LangChain for tool-augmented LLM workflows
- AutoGen for multi-agent systems
- Vector databases for semantic search and retrieval

The backend architecture separates AI services from core infrastructure, allowing models, agents, and storage layers to evolve independently.

services/
└── ai/
    ├── router.py
    ├── schemas.py
    ├── agents/
    │   └── __init__.py
    ├── models/
    │   └── __init__.py
    └── tools/
        └── __init__.py


---

Blogs:
React Blogs Page
   ↓ GET /api/blogs
FastAPI Blogs Service
   ↓
blogs.json (temporary storage)

Backend endpoints (minimal, complete)
GET  /api/blogs              # list all blogs
GET  /api/blogs/{slug}       # get one blog
POST /api/blogs              # create blog (you only)

Backend storage (simple JSON)
backend/data/blogs.json
