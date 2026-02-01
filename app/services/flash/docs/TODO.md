# Flash Service - TODO List

## 🔴 Critical: Database Implementation Required

### Current State
The Flash service is **NOT production-ready** because it lacks persistent storage. All user data, profiles, and application history are currently **hardcoded mocks** or **placeholders**.

### Why Database is Needed

#### 1. User Profile Management
**Model**: `UserProfile` (models.py:197-218)
- Store user personal info, skills, experience
- Track master resume paths
- Work authorization details
- Created/updated timestamps

**Current Issues**:
- Lines 90, 150, 202 in `router.py`: Hardcoded mock profiles
- No persistence between requests
- Cannot support multiple users

#### 2. Application History & Logging
**Model**: `ApplicationLog` (models.py:227-236)
- Track all job applications submitted
- Status tracking: pending → in_progress → submitted
- Analytics on application success rates
- Learning from past approved answers

**Current Issues**:
- Line 349 in `router.py`: Returns empty list `[]`
- No application history available
- Cannot learn from past submissions

#### 3. Application Reviews
**Model**: `ApplicationReview` (models.py:158-171)
- Store filled application forms before submission
- Track user edits and approvals
- Validation warnings and status
- Resume versions used

**Current Issues**:
- Line 328 in `router.py`: `# Fetch application from database` (commented out)
- Applications lost if user closes browser
- No draft saving capability

#### 4. Job Analysis Caching
**Model**: `JobAnalysis` (models.py:49-59)
- Cache analyzed job descriptions
- Avoid re-analyzing same jobs
- Store match scores and requirements

**Current Issues**:
- Re-analyzes same jobs (expensive LLM calls)
- No job analysis history
- Cannot track which jobs user applied to

#### 5. Vector Store for RAG (Question Answering)
**Service**: `QuestionAnsweringService` (services/qa_engine.py)
- Store past approved answers as embeddings
- Semantic search for similar questions
- Knowledge base for resume content
- Learning from user corrections

**Current Issues**:
- Line 39 in `qa_engine.py`: `self.vector_store = None`
- Cannot retrieve past answers
- No semantic similarity search
- RAG system incomplete

---

## 📋 Implementation Plan

### Phase 1: SQLite + FAISS (Quick Start)
**Recommended for**: Development, single-user, local testing

**Tasks**:
- [ ] Create SQLite schema for:
  - `users` table (UserProfile)
  - `applications` table (ApplicationLog)
  - `application_reviews` table (ApplicationReview)
  - `job_analyses` table (JobAnalysis)
- [ ] Create `database.py` with SQLAlchemy models
- [ ] Create `crud.py` with CRUD operations
- [ ] Add FAISS vector store integration
  - Store embeddings in `data/knowledge_base/faiss_index/`
  - Index past answers and resume content
- [ ] Update `router.py` to use real database calls:
  - Replace line 90: `user_profile = fetch_user_profile(request.user_id)`
  - Replace line 328: `application = fetch_application(request.application_id)`
  - Replace line 349: Return actual application logs
- [ ] Add database initialization script
- [ ] Update requirements.txt:
  ```
  sqlalchemy>=2.0.0
  aiosqlite>=0.19.0
  faiss-cpu>=1.8.0
  ```

**Database Location**: `data/flash/flash.db`

---

### Phase 2: PostgreSQL + pgvector (Production)
**Recommended for**: Multi-user, production deployment, scaling

**Tasks**:
- [ ] Set up PostgreSQL database
- [ ] Install pgvector extension
- [ ] Migrate schema from SQLite to Postgres
- [ ] Update connection strings in `config.py`
- [ ] Replace FAISS with pgvector for embeddings
- [ ] Add connection pooling
- [ ] Add database migrations (Alembic)
- [ ] Update requirements.txt:
  ```
  asyncpg>=0.29.0
  psycopg2-binary>=2.9.9
  pgvector>=0.2.0
  alembic>=1.13.0
  ```

**Connection String**: Set in `.env` as `DATABASE_URL`

---

## 📊 Database Schema (Proposed)

### Users Table
```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    location VARCHAR(255),
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    current_title VARCHAR(255),
    years_of_experience INTEGER,
    skills JSON,
    preferred_roles JSON,
    work_authorization VARCHAR(100),
    master_resume_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Applications Table
```sql
CREATE TABLE applications (
    application_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    job_id VARCHAR(255),
    company VARCHAR(255),
    role VARCHAR(255),
    resume_version VARCHAR(500),
    answers_count INTEGER,
    status VARCHAR(50),
    submitted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Application Reviews Table
```sql
CREATE TABLE application_reviews (
    application_id VARCHAR(255) PRIMARY KEY,
    job_id VARCHAR(255),
    user_id VARCHAR(255) REFERENCES users(user_id),
    company VARCHAR(255),
    role VARCHAR(255),
    filled_fields JSON,
    resume_path VARCHAR(500),
    status VARCHAR(50),
    ready_for_submission BOOLEAN,
    warnings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Job Analyses Table
```sql
CREATE TABLE job_analyses (
    job_id VARCHAR(255) PRIMARY KEY,
    required_skills JSON,
    preferred_skills JSON,
    technologies JSON,
    seniority_level VARCHAR(100),
    role_focus VARCHAR(100),
    key_requirements JSON,
    match_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Vector Embeddings Table (pgvector)
```sql
CREATE TABLE answer_embeddings (
    id SERIAL PRIMARY KEY,
    question TEXT,
    answer TEXT,
    embedding vector(1536),  -- OpenAI embedding dimension
    user_id VARCHAR(255) REFERENCES users(user_id),
    approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON answer_embeddings USING ivfflat (embedding vector_cosine_ops);
```

---

## 🚨 Files That Need Updates

### Priority 1: Database Core
- [ ] **NEW**: `app/services/flash/database.py` - SQLAlchemy models
- [ ] **NEW**: `app/services/flash/crud.py` - CRUD operations
- [ ] **NEW**: `app/services/flash/db_init.py` - Database initialization
- [ ] **UPDATE**: `app/services/flash/config.py` - Add DB connection config

### Priority 2: Router Updates
- [ ] **UPDATE**: `app/services/flash/router.py`
  - Line 90: Replace mock profile with DB fetch
  - Line 150: Replace mock profile with DB fetch  
  - Line 202: Replace mock profile with DB fetch
  - Line 328: Replace comment with DB fetch
  - Line 341: Add user edit persistence
  - Line 349: Return real application logs from DB
  - Add endpoints: `POST /profile`, `PUT /profile/{user_id}`, `DELETE /profile/{user_id}`

### Priority 3: Service Updates
- [ ] **UPDATE**: `app/services/flash/services/qa_engine.py`
  - Line 39: Initialize vector store (FAISS/pgvector)
  - Add embedding generation
  - Add similarity search
  - Store approved answers

### Priority 4: Configuration
- [ ] **UPDATE**: `requirements.txt` - Add database dependencies
- [ ] **UPDATE**: `.env.flash.example` - Add database connection strings

---

## ⚠️ Current Placeholders to Replace

### router.py
```python
# Line 90
# user_profile = fetch_user_profile(request.user_id)  ← IMPLEMENT THIS

# Line 150
# user_profile = fetch_user_profile(request.user_id)  ← IMPLEMENT THIS

# Line 328
# application = fetch_application(request.application_id)  ← IMPLEMENT THIS

# Line 341
# Update fields with user edits  ← IMPLEMENT PERSISTENCE

# Line 349 - get_applications endpoint
return []  ← QUERY DATABASE INSTEAD
```

---

## 🎯 Quick Start Command (When Implementing)

```bash
# Install database dependencies
pip install sqlalchemy aiosqlite faiss-cpu

# Run database initialization
python -m app.services.flash.db_init

# Test database connection
python -c "from app.services.flash.database import init_db; init_db()"
```

---

## 📝 Notes
- Start with **SQLite + FAISS** for quick prototyping
- Migrate to **Postgres + pgvector** when deploying
- Vector store is critical for RAG-based Q&A to work properly
- Without database, Flash is a **stateless demo** only
- Consider adding Redis for session caching later

---

## 🔗 Related Files
- [router.py](./router.py) - Contains all placeholder comments
- [models.py](./models.py) - All Pydantic models that need DB mapping
- [qa_engine.py](./services/qa_engine.py) - Needs vector store integration
- [config.py](./config.py) - Needs database connection settings

**Last Updated**: February 1, 2026
