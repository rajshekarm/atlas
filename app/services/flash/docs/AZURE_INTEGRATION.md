# Azure Integration Guide - Flash Service

## 📚 Table of Contents
1. [Overview](#overview)
2. [Azure Services Used](#azure-services-used)
3. [Azure OpenAI](#azure-openai)
4. [Azure AI Search](#azure-ai-search)
5. [Azure Blob Storage](#azure-blob-storage)
6. [Configuration & Authentication](#configuration--authentication)
7. [Setup Guide](#setup-guide)
8. [Code Examples](#code-examples)
9. [Cost Optimization](#cost-optimization)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Flash service leverages **3 core Azure services** to power its AI-driven job application assistant:

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLASH SERVICE                                │
│                                                                   │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │ Job Analyzer │   │Resume Tailor │   │  QA Engine   │        │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘        │
│         │                   │                   │                 │
└─────────┼───────────────────┼───────────────────┼─────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AZURE CLOUD                               │
│                                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ Azure OpenAI   │  │ Azure AI Search│  │ Azure Blob      │  │
│  │ (GPT-4)        │  │ (Vector DB)    │  │ Storage         │  │
│  │                │  │                │  │                 │  │
│  │ • Job analysis │  │ • Store Q&A    │  │ • Store resumes │  │
│  │ • Resume edit  │  │ • Semantic     │  │ • Version       │  │
│  │ • Answer gen   │  │   search       │  │   control       │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Why Azure?**
- ✅ Enterprise-grade security and compliance
- ✅ Seamless integration between services
- ✅ Scalable infrastructure
- ✅ Pay-as-you-go pricing
- ✅ Built-in monitoring and logging

---

## Azure Services Used

### 1. **Azure OpenAI Service** 🤖
**Purpose**: LLM-powered text generation and analysis

**Use Cases in Flash**:
- Analyze job descriptions → extract skills, requirements
- Tailor resume content → emphasize relevant experience
- Answer application questions → generate truthful responses
- Improve answer quality → refine low-confidence answers

**Model**: GPT-4 (or GPT-4-Turbo)  
**API Version**: 2024-02-01  
**Endpoint**: `https://<your-resource>.openai.azure.com/`

---

### 2. **Azure AI Search** 🔍
**Purpose**: Vector database for RAG (Retrieval-Augmented Generation)

**Use Cases in Flash**:
- Store past approved answers with embeddings
- Semantic search for similar questions
- Retrieve relevant context for answer generation
- Learn from user's application history

**Index Schema**: `flash-knowledge-base`  
**Search Type**: Hybrid (keyword + vector)  
**Endpoint**: `https://<your-search>.search.windows.net`

---

### 3. **Azure Blob Storage** 💾
**Purpose**: Persistent storage for documents

**Use Cases in Flash**:
- Store master resumes (user uploads)
- Store tailored resume versions
- Version control for resume edits
- Backup and archival

**Container**: `resumes`  
**Access**: Private with SAS tokens  
**Endpoint**: `https://<your-account>.blob.core.windows.net/`

---

## Azure OpenAI

### Architecture

```
Flash Service
    │
    ├─→ Job Analyzer
    │   └─→ Azure OpenAI
    │       • Model: GPT-4
    │       • Task: Extract skills from job description
    │       • Prompt: "Analyze this job posting and extract..."
    │       • Response: Structured JSON with skills list
    │
    ├─→ Resume Tailor
    │   └─→ Azure OpenAI
    │       • Model: GPT-4
    │       • Task: Rewrite resume section
    │       • Prompt: "Rewrite this section to emphasize..."
    │       • Guardrails: No fake experience, no date changes
    │
    └─→ QA Engine
        └─→ Azure OpenAI
            • Model: GPT-4
            • Task: Answer question with context
            • Prompt: "Based on this resume, answer..."
            • Context: Retrieved from profile + resume + past answers
```

### How Flash Uses Azure OpenAI

#### 1. **Job Analysis** (`job_analyzer.py`)

**Scenario**: User applies to "Senior Backend Engineer" role

```python
async def _extract_skills(self, text_list: List[str]) -> List[str]:
    """
    Use Azure OpenAI to extract skills from job description
    """
    combined_text = " ".join(text_list)
    
    # Build prompt
    prompt = f"""
    Extract technical and professional skills from the following job requirements.
    Return only the skill names, one per line.
    
    Requirements:
    {combined_text}
    
    Skills:
    """
    
    # Call Azure OpenAI
    response = await self.llm_client.chat.completions.create(
        model="gpt-4",  # Your deployment name
        messages=[
            {"role": "system", "content": "You are a job requirements analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Lower = more focused
        max_tokens=500
    )
    
    skills = response.choices[0].message.content.split('\n')
    return [s.strip() for s in skills if s.strip()]
```

**Input**:
```
Requirements:
- 5+ years of Python experience
- Expert in FastAPI framework
- PostgreSQL database knowledge
- AWS cloud experience
```

**Azure OpenAI Response**:
```
Python
FastAPI
PostgreSQL
AWS
Backend Development
API Design
Database Management
```

---

#### 2. **Resume Tailoring** (`resume_tailor.py`)

**Scenario**: Tailor user's resume to match job requirements

```python
async def _tailor_section(
    self,
    section: ResumeSection,
    job_analysis: JobAnalysis
) -> ResumeSection:
    """
    Use Azure OpenAI to rewrite resume section with guardrails
    """
    
    prompt = f"""
You are an ethical resume editor. Rewrite the following resume section to better match a job description.

STRICT RULES (GUARDRAILS):
1. DO NOT add any new skills or experiences
2. DO NOT change dates, company names, or job titles
3. DO NOT fabricate or exaggerate
4. ONLY rephrase existing content to emphasize relevant aspects

TARGET JOB:
- Required Skills: {', '.join(job_analysis.required_skills)}
- Technologies: {', '.join(job_analysis.technologies)}

RESUME SECTION:
{section.original_content}

INSTRUCTIONS:
Rewrite to emphasize skills that match the target job.
Only rephrase - do not add new information.

TAILORED SECTION:
"""
    
    response = await self.llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,  # Moderate creativity
        max_tokens=1000
    )
    
    tailored_content = response.choices[0].message.content
    
    # Validate with guardrails before returning
    if self._validate_changes(section, tailored_content):
        return tailored_content
    else:
        return section.original_content  # Reject if validation fails
```

**Input**:
```
EXPERIENCE:
Developed backend services using Python and various frameworks.
Built APIs for client applications.
```

**Azure OpenAI Response** (when job requires FastAPI):
```
EXPERIENCE:
Architected and developed scalable backend services using Python, with extensive
experience in FastAPI framework for building high-performance RESTful APIs.
Designed and implemented robust API solutions for client applications, ensuring
reliability and maintainability.
```

---

#### 3. **Question Answering** (`qa_engine.py`)

**Scenario**: Answer "Why do you want to work at our company?"

```python
async def _generate_answer(
    self,
    context: QuestionContext,
    retrieved_sources: List[AnswerSource],
    user_profile: UserProfile
) -> tuple[str, float]:
    """
    Generate answer using Azure OpenAI with RAG context
    """
    
    # Build RAG prompt
    prompt = f"""
You are helping a user fill out a job application. Answer the following question
truthfully and professionally based ONLY on the provided context.

QUESTION:
{context.question}

AVAILABLE CONTEXT:
"""
    
    for i, source in enumerate(retrieved_sources, 1):
        prompt += f"\n{i}. From {source.source_type} (relevance: {source.relevance_score:.2f}):\n"
        prompt += f"{source.content}\n"
    
    prompt += f"""
USER PROFILE:
- Name: {user_profile.full_name}
- Current Title: {user_profile.current_title}
- Experience: {user_profile.years_of_experience} years

INSTRUCTIONS:
1. Answer truthfully based only on the provided context
2. Do not fabricate information
3. Keep the answer concise and professional (2-3 sentences)
4. Match the tone expected for a job application

ANSWER:
"""
    
    response = await self.llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=300
    )
    
    answer = response.choices[0].message.content
    
    # Calculate confidence based on source quality
    avg_relevance = sum(s.relevance_score for s in retrieved_sources) / len(retrieved_sources)
    confidence = min(avg_relevance, 0.85)
    
    return answer, confidence
```

---

### Azure OpenAI Configuration

#### In `config.py`:
```python
from pydantic import BaseSettings

class FlashSettings(BaseSettings):
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = "https://your-resource.openai.azure.com/"
    azure_openai_api_key: str = "your-api-key"
    azure_openai_deployment_name: str = "gpt-4"
    azure_openai_api_version: str = "2024-02-01"
    
    class Config:
        env_file = ".env"
        env_prefix = "FLASH_"
```

#### Client Initialization:
```python
from openai import AzureOpenAI

# Initialize Azure OpenAI client
llm_client = AzureOpenAI(
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    azure_endpoint=settings.azure_openai_endpoint
)

# Pass to services
job_analyzer = JobAnalyzerService(llm_client=llm_client)
resume_tailor = ResumeTailorService(llm_client=llm_client)
qa_engine = QuestionAnsweringService(llm_client=llm_client)
```

---

## Azure AI Search

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AZURE AI SEARCH INDEX                         │
│                   "flash-knowledge-base"                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Document Structure:                                             │
│  {                                                               │
│    "id": "ans_123abc",                                           │
│    "question": "What is your email?",                            │
│    "answer": "john.doe@email.com",                               │
│    "embedding": [0.123, -0.456, ...],  // 1536-dimensional      │
│    "user_id": "user_789",                                        │
│    "job_id": "job_456",                                          │
│    "company": "Tech Corp",                                       │
│    "timestamp": "2026-02-01T10:30:00Z",                          │
│    "confidence": 0.95,                                           │
│    "approved": true                                              │
│  }                                                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### How Flash Uses Azure AI Search

#### 1. **Storing Approved Answers**

When user approves an application, answers are stored for future use:

```python
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# Initialize clients
search_client = SearchClient(
    endpoint=settings.azure_search_endpoint,
    index_name=settings.azure_search_index_name,
    credential=AzureKeyCredential(settings.azure_search_api_key)
)

openai_client = AzureOpenAI(...)

async def store_approved_answer(
    question: str,
    answer: str,
    metadata: Dict[str, Any]
):
    """
    Store approved answer in Azure AI Search with embedding
    """
    
    # Generate embedding for semantic search
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-ada-002",  # Embedding model
        input=question
    )
    embedding = embedding_response.data[0].embedding
    
    # Create document
    document = {
        "id": f"ans_{uuid.uuid4().hex[:8]}",
        "question": question,
        "answer": answer,
        "embedding": embedding,
        "user_id": metadata.get("user_id"),
        "job_id": metadata.get("job_id"),
        "company": metadata.get("company"),
        "timestamp": datetime.now().isoformat(),
        "confidence": metadata.get("confidence", 0.8),
        "approved": True
    }
    
    # Upload to Azure AI Search
    result = search_client.upload_documents(documents=[document])
    
    print(f"Stored answer with ID: {document['id']}")
    return result
```

---

#### 2. **Semantic Search for Similar Questions**

When answering a new question, search for similar past answers:

```python
from azure.search.documents.models import VectorizedQuery

async def search_past_answers(question: str, top_k: int = 3) -> List[AnswerSource]:
    """
    Search Azure AI Search for similar past questions using vector search
    """
    
    # Generate embedding for query
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=question
    )
    query_embedding = embedding_response.data[0].embedding
    
    # Perform vector search
    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=top_k,
        fields="embedding"
    )
    
    results = search_client.search(
        search_text=None,  # Pure vector search
        vector_queries=[vector_query],
        select=["question", "answer", "confidence", "company"],
        filter="approved eq true"  # Only approved answers
    )
    
    # Convert to AnswerSource objects
    sources = []
    for result in results:
        sources.append(AnswerSource(
            source_type="past_answer",
            content=result["answer"],
            relevance_score=result["@search.score"]  # Cosine similarity
        ))
    
    return sources
```

**Example Search**:
```
Query: "What is your experience with Python?"

Results:
1. Question: "Describe your Python expertise"
   Answer: "I have 5+ years of Python development..."
   Score: 0.89 (very similar)

2. Question: "How long have you used Python?"
   Answer: "I've been working with Python since 2018..."
   Score: 0.82

3. Question: "What programming languages do you know?"
   Answer: "Python, JavaScript, TypeScript..."
   Score: 0.71
```

---

#### 3. **Hybrid Search (Keyword + Vector)**

Combine keyword and semantic search for best results:

```python
async def hybrid_search(question: str, top_k: int = 5) -> List[AnswerSource]:
    """
    Hybrid search: keyword (BM25) + vector (semantic)
    """
    
    # Generate embedding
    embedding = generate_embedding(question)
    
    # Create vector query
    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=top_k,
        fields="embedding"
    )
    
    # Hybrid search
    results = search_client.search(
        search_text=question,  # Keyword search
        vector_queries=[vector_query],  # Semantic search
        select=["question", "answer", "confidence"],
        top=top_k,
        query_type="semantic",  # Enable semantic ranking
        filter="approved eq true"
    )
    
    return process_results(results)
```

---

### Azure AI Search Index Schema

```json
{
  "name": "flash-knowledge-base",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true,
      "searchable": false
    },
    {
      "name": "question",
      "type": "Edm.String",
      "searchable": true,
      "analyzer": "en.microsoft"
    },
    {
      "name": "answer",
      "type": "Edm.String",
      "searchable": true
    },
    {
      "name": "embedding",
      "type": "Collection(Edm.Single)",
      "searchable": true,
      "dimensions": 1536,
      "vectorSearchProfile": "my-vector-profile"
    },
    {
      "name": "user_id",
      "type": "Edm.String",
      "filterable": true
    },
    {
      "name": "job_id",
      "type": "Edm.String",
      "filterable": true
    },
    {
      "name": "company",
      "type": "Edm.String",
      "filterable": true,
      "facetable": true
    },
    {
      "name": "timestamp",
      "type": "Edm.DateTimeOffset",
      "filterable": true,
      "sortable": true
    },
    {
      "name": "confidence",
      "type": "Edm.Double",
      "filterable": true
    },
    {
      "name": "approved",
      "type": "Edm.Boolean",
      "filterable": true
    }
  ],
  "vectorSearch": {
    "profiles": [
      {
        "name": "my-vector-profile",
        "algorithm": "my-hnsw-config"
      }
    ],
    "algorithms": [
      {
        "name": "my-hnsw-config",
        "kind": "hnsw",
        "hnswParameters": {
          "metric": "cosine",
          "m": 4,
          "efConstruction": 400,
          "efSearch": 500
        }
      }
    ]
  }
}
```

---

## Azure Blob Storage

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              AZURE BLOB STORAGE - "resumes" Container            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Folder Structure:                                               │
│                                                                   │
│  /resumes/                                                       │
│    ├── users/                                                    │
│    │   ├── user_123/                                             │
│    │   │   ├── master_resume.pdf                                │
│    │   │   ├── master_resume.txt                                │
│    │   │   └── versions/                                        │
│    │   │       ├── resume_tailored_job456_20260201.txt          │
│    │   │       ├── resume_tailored_job789_20260201.txt          │
│    │   │       └── ...                                          │
│    │   │                                                         │
│    │   └── user_456/                                             │
│    │       └── ...                                               │
│    │                                                             │
│    └── temp/                                                     │
│        └── uploads/  (pending processing)                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### How Flash Uses Azure Blob Storage

#### 1. **Upload Master Resume**

```python
from azure.storage.blob import BlobServiceClient, BlobClient

# Initialize client
blob_service_client = BlobServiceClient.from_connection_string(
    settings.azure_storage_connection_string
)

async def upload_master_resume(
    user_id: str,
    resume_file: UploadFile
) -> str:
    """
    Upload user's master resume to Azure Blob Storage
    """
    
    # Read file content
    content = await resume_file.read()
    
    # Generate blob path
    blob_name = f"users/{user_id}/master_resume.txt"
    
    # Get blob client
    blob_client = blob_service_client.get_blob_client(
        container="resumes",
        blob=blob_name
    )
    
    # Upload with metadata
    blob_client.upload_blob(
        content,
        overwrite=True,
        metadata={
            "user_id": user_id,
            "original_filename": resume_file.filename,
            "upload_date": datetime.now().isoformat(),
            "content_type": resume_file.content_type
        }
    )
    
    # Return blob URL
    return blob_client.url
```

---

#### 2. **Store Tailored Resume Versions**

```python
async def save_tailored_resume(
    user_id: str,
    job_id: str,
    tailored_content: str
) -> str:
    """
    Save tailored resume version to Blob Storage
    """
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    blob_name = f"users/{user_id}/versions/resume_tailored_{job_id}_{timestamp}.txt"
    
    # Get blob client
    blob_client = blob_service_client.get_blob_client(
        container="resumes",
        blob=blob_name
    )
    
    # Upload
    blob_client.upload_blob(
        tailored_content,
        metadata={
            "user_id": user_id,
            "job_id": job_id,
            "created_at": datetime.now().isoformat(),
            "type": "tailored"
        }
    )
    
    return blob_client.url
```

---

#### 3. **Download Resume for Processing**

```python
async def get_resume_content(user_id: str) -> str:
    """
    Download master resume from Blob Storage
    """
    
    blob_name = f"users/{user_id}/master_resume.txt"
    
    blob_client = blob_service_client.get_blob_client(
        container="resumes",
        blob=blob_name
    )
    
    # Download
    stream = blob_client.download_blob()
    content = stream.readall().decode('utf-8')
    
    return content
```

---

#### 4. **Generate SAS Token for Secure Access**

```python
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import timedelta

def generate_resume_download_link(
    user_id: str,
    blob_name: str,
    expiry_hours: int = 24
) -> str:
    """
    Generate temporary download link with SAS token
    """
    
    # Generate SAS token
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name="resumes",
        blob_name=blob_name,
        account_key=settings.azure_storage_account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
    )
    
    # Build URL with SAS
    blob_client = blob_service_client.get_blob_client(
        container="resumes",
        blob=blob_name
    )
    
    url_with_sas = f"{blob_client.url}?{sas_token}"
    return url_with_sas
```

---

#### 5. **List Resume Versions**

```python
async def list_resume_versions(user_id: str) -> List[Dict]:
    """
    List all tailored resume versions for a user
    """
    
    container_client = blob_service_client.get_container_client("resumes")
    
    # List blobs with prefix
    blob_list = container_client.list_blobs(
        name_starts_with=f"users/{user_id}/versions/"
    )
    
    versions = []
    for blob in blob_list:
        versions.append({
            "name": blob.name,
            "size": blob.size,
            "created": blob.creation_time,
            "metadata": blob.metadata
        })
    
    return versions
```

---

## Configuration & Authentication

### Environment Variables (`.env`)

```bash
# ===== Azure OpenAI =====
FLASH_AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
FLASH_AZURE_OPENAI_API_KEY=1234567890abcdef1234567890abcdef
FLASH_AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
FLASH_AZURE_OPENAI_API_VERSION=2024-02-01

# ===== Azure AI Search =====
FLASH_AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
FLASH_AZURE_SEARCH_API_KEY=9876543210fedcba9876543210fedcba
FLASH_AZURE_SEARCH_INDEX_NAME=flash-knowledge-base

# ===== Azure Blob Storage =====
FLASH_AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=youraccount;AccountKey=yourkey;EndpointSuffix=core.windows.net
FLASH_AZURE_STORAGE_CONTAINER_NAME=resumes
```

### Authentication Methods

#### Method 1: API Keys (Current Implementation)
```python
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# OpenAI with API key
openai_client = AzureOpenAI(
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    azure_endpoint=settings.azure_openai_endpoint
)

# AI Search with API key
search_client = SearchClient(
    endpoint=settings.azure_search_endpoint,
    index_name=settings.azure_search_index_name,
    credential=AzureKeyCredential(settings.azure_search_api_key)
)
```

#### Method 2: Managed Identity (Production Recommended)
```python
from azure.identity import DefaultAzureCredential

# Use managed identity (no keys needed!)
credential = DefaultAzureCredential()

# OpenAI with managed identity
openai_client = AzureOpenAI(
    azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token,
    api_version=settings.azure_openai_api_version,
    azure_endpoint=settings.azure_openai_endpoint
)

# AI Search with managed identity
search_client = SearchClient(
    endpoint=settings.azure_search_endpoint,
    index_name=settings.azure_search_index_name,
    credential=credential
)

# Blob Storage with managed identity
blob_service_client = BlobServiceClient(
    account_url=f"https://{account_name}.blob.core.windows.net",
    credential=credential
)
```

---

## Setup Guide

### Step 1: Create Azure Resources

#### A. Azure OpenAI
```bash
# Create resource group
az group create --name flash-rg --location eastus

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name flash-openai \
  --resource-group flash-rg \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Deploy GPT-4 model
az cognitiveservices account deployment create \
  --name flash-openai \
  --resource-group flash-rg \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"

# Get endpoint and key
az cognitiveservices account show \
  --name flash-openai \
  --resource-group flash-rg \
  --query "properties.endpoint"

az cognitiveservices account keys list \
  --name flash-openai \
  --resource-group flash-rg
```

#### B. Azure AI Search
```bash
# Create AI Search service
az search service create \
  --name flash-search \
  --resource-group flash-rg \
  --sku standard \
  --location eastus

# Get admin key
az search admin-key show \
  --service-name flash-search \
  --resource-group flash-rg
```

#### C. Azure Blob Storage
```bash
# Create storage account
az storage account create \
  --name flashstorage123 \
  --resource-group flash-rg \
  --location eastus \
  --sku Standard_LRS

# Create container
az storage container create \
  --name resumes \
  --account-name flashstorage123

# Get connection string
az storage account show-connection-string \
  --name flashstorage123 \
  --resource-group flash-rg
```

---

### Step 2: Create AI Search Index

```python
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *

# Initialize index client
index_client = SearchIndexClient(
    endpoint=settings.azure_search_endpoint,
    credential=AzureKeyCredential(settings.azure_search_api_key)
)

# Define index schema
index = SearchIndex(
    name="flash-knowledge-base",
    fields=[
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="question", type=SearchFieldDataType.String),
        SearchableField(name="answer", type=SearchFieldDataType.String),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="my-vector-profile"
        ),
        SimpleField(name="user_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="job_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="company", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="timestamp", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        SimpleField(name="confidence", type=SearchFieldDataType.Double, filterable=True),
        SimpleField(name="approved", type=SearchFieldDataType.Boolean, filterable=True)
    ],
    vector_search=VectorSearch(
        profiles=[
            VectorSearchProfile(
                name="my-vector-profile",
                algorithm_configuration_name="my-hnsw-config"
            )
        ],
        algorithms=[
            HnswAlgorithmConfiguration(
                name="my-hnsw-config",
                parameters=HnswParameters(
                    metric="cosine",
                    m=4,
                    ef_construction=400,
                    ef_search=500
                )
            )
        ]
    )
)

# Create index
result = index_client.create_index(index)
print(f"Index '{result.name}' created successfully!")
```

---

### Step 3: Update Flash Configuration

```python
# app/services/flash/config.py

from pydantic import BaseSettings
from typing import Optional

class FlashSettings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment_name: str = "gpt-4"
    azure_openai_api_version: str = "2024-02-01"
    
    # Azure AI Search
    azure_search_endpoint: Optional[str] = None
    azure_search_api_key: Optional[str] = None
    azure_search_index_name: str = "flash-knowledge-base"
    
    # Azure Blob Storage
    azure_storage_connection_string: Optional[str] = None
    azure_storage_container_name: str = "resumes"
    
    class Config:
        env_file = ".env"
        env_prefix = "FLASH_"

settings = FlashSettings()
```

---

### Step 4: Initialize Azure Clients

```python
# app/services/flash/azure_clients.py

from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from app.services.flash.config import settings

class AzureClients:
    """Singleton for Azure service clients"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        # Azure OpenAI
        if settings.azure_openai_endpoint and settings.azure_openai_api_key:
            self.openai_client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
        else:
            self.openai_client = None
        
        # Azure AI Search
        if settings.azure_search_endpoint and settings.azure_search_api_key:
            self.search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index_name,
                credential=AzureKeyCredential(settings.azure_search_api_key)
            )
        else:
            self.search_client = None
        
        # Azure Blob Storage
        if settings.azure_storage_connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                settings.azure_storage_connection_string
            )
        else:
            self.blob_service_client = None

# Global instance
azure_clients = AzureClients()
```

---

## Code Examples

### Complete End-to-End Example

```python
from app.services.flash.azure_clients import azure_clients
from app.services.flash.services.qa_engine import QuestionAnsweringService
from app.services.flash.models import QuestionContext, FieldType, UserProfile

async def answer_application_question_example():
    """
    Complete example: Answer a job application question using all Azure services
    """
    
    # 1. User data (stored in your database)
    user_profile = UserProfile(
        user_id="user_123",
        full_name="John Doe",
        email="john.doe@email.com",
        current_title="Senior Software Engineer",
        years_of_experience=5,
        skills=["Python", "FastAPI", "PostgreSQL"],
        master_resume_path="users/user_123/master_resume.txt"
    )
    
    # 2. Download resume from Azure Blob Storage
    blob_client = azure_clients.blob_service_client.get_blob_client(
        container="resumes",
        blob=user_profile.master_resume_path
    )
    resume_content = blob_client.download_blob().readall().decode('utf-8')
    
    # 3. Question context
    question_context = QuestionContext(
        question="What is your experience with Python?",
        field_id="python_experience",
        field_type=FieldType.TEXTAREA,
        job_id="job_abc123"
    )
    
    # 4. Initialize QA Engine with Azure clients
    qa_engine = QuestionAnsweringService(
        llm_client=azure_clients.openai_client,
        vector_store=azure_clients.search_client
    )
    
    # 5. Answer question (uses Azure OpenAI + Azure AI Search)
    answer = await qa_engine.answer_question(
        context=question_context,
        user_profile=user_profile
    )
    
    print(f"Question: {answer.question}")
    print(f"Answer: {answer.answer}")
    print(f"Confidence: {answer.confidence} ({answer.confidence_score:.2f})")
    print(f"Sources: {[s.source_type for s in answer.sources]}")
    
    # 6. If approved, store in Azure AI Search for future use
    if answer.confidence_score > 0.7:
        await qa_engine.store_approved_answer(
            question=answer.question,
            answer=answer.answer,
            metadata={
                "user_id": user_profile.user_id,
                "job_id": question_context.job_id,
                "confidence": answer.confidence_score
            }
        )
    
    return answer
```

---

## Cost Optimization

### 1. **Azure OpenAI Costs**

**Pricing** (as of 2026):
- GPT-4 Input: $0.03 per 1K tokens
- GPT-4 Output: $0.06 per 1K tokens
- Embeddings: $0.0001 per 1K tokens

**Optimization Strategies**:

```python
# Cache LLM responses
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
async def cached_llm_call(prompt_hash: str, prompt: str):
    """Cache LLM responses for identical prompts"""
    response = await llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3  # Lower temp = more deterministic = better caching
    )
    return response.choices[0].message.content

# Use embeddings cache
embeddings_cache = {}

def get_cached_embedding(text: str):
    """Cache embeddings to avoid regenerating"""
    text_hash = hashlib.md5(text.encode()).hexdigest()
    
    if text_hash not in embeddings_cache:
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embeddings_cache[text_hash] = response.data[0].embedding
    
    return embeddings_cache[text_hash]
```

**Token Optimization**:
```python
# Limit context size
def truncate_context(context: str, max_tokens: int = 1000) -> str:
    """Truncate context to save tokens"""
    words = context.split()
    # Rough estimate: 1 token ≈ 0.75 words
    max_words = int(max_tokens * 0.75)
    return ' '.join(words[:max_words])

# Use shorter prompts
prompt = f"Answer based on: {truncate_context(resume)}"
```

---

### 2. **Azure AI Search Costs**

**Pricing**:
- Standard tier: ~$250/month
- Query costs: Included in tier pricing

**Optimization**:
```python
# Limit search results
results = search_client.search(
    search_text=query,
    top=3,  # Only retrieve top 3 results
    select=["question", "answer"]  # Only fetch needed fields
)

# Use filters to reduce search scope
results = search_client.search(
    search_text=query,
    filter=f"user_id eq '{user_id}' and timestamp ge 2026-01-01",  # Limit scope
    top=5
)
```

---

### 3. **Azure Blob Storage Costs**

**Pricing**:
- Storage: $0.018 per GB/month (LRS)
- Operations: ~$0.004 per 10,000 writes

**Optimization**:
```python
# Compress large resumes
import gzip

def upload_compressed(content: bytes, blob_name: str):
    """Upload compressed data to save storage"""
    compressed = gzip.compress(content)
    
    blob_client.upload_blob(
        compressed,
        metadata={"compressed": "gzip"}
    )

# Delete old versions
async def cleanup_old_versions(user_id: str, keep_latest: int = 5):
    """Delete old tailored resume versions to save storage"""
    versions = await list_resume_versions(user_id)
    
    # Sort by creation time
    versions.sort(key=lambda v: v['created'], reverse=True)
    
    # Delete old ones
    for version in versions[keep_latest:]:
        blob_client = blob_service_client.get_blob_client(
            container="resumes",
            blob=version['name']
        )
        blob_client.delete_blob()
```

---

## Troubleshooting

### Common Issues

#### 1. **Azure OpenAI: Rate Limiting**
```
Error: 429 Too Many Requests
```

**Solution**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_openai_with_retry(prompt: str):
    """Retry with exponential backoff"""
    return await llm_client.chat.completions.create(...)
```

#### 2. **Azure AI Search: Index Not Found**
```
Error: The specified index does not exist
```

**Solution**:
```python
# Check if index exists before querying
from azure.search.documents.indexes import SearchIndexClient

index_client = SearchIndexClient(...)

try:
    index = index_client.get_index("flash-knowledge-base")
    print("Index exists!")
except Exception:
    print("Index not found. Creating...")
    # Create index (see setup guide)
```

#### 3. **Azure Blob Storage: Authentication Failed**
```
Error: AuthenticationFailed - Server failed to authenticate the request
```

**Solution**:
```python
# Verify connection string format
connection_string = "DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"

# Test connection
try:
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    containers = list(blob_service_client.list_containers())
    print(f"Connected! Found {len(containers)} containers")
except Exception as e:
    print(f"Connection failed: {e}")
```

---

## Summary

**Flash Service + Azure = Powerful AI Job Assistant**

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION SUMMARY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Azure OpenAI (GPT-4)                                         │
│     ✅ Job analysis: Extract skills from descriptions            │
│     ✅ Resume tailoring: Rewrite with guardrails                 │
│     ✅ Answer generation: RAG-powered responses                  │
│     💰 Cost: ~$0.03-0.06 per 1K tokens                           │
│                                                                   │
│  2. Azure AI Search (Vector DB)                                  │
│     ✅ Store past approved answers                               │
│     ✅ Semantic search for similar questions                     │
│     ✅ Hybrid search (keyword + vector)                          │
│     💰 Cost: ~$250/month (Standard tier)                         │
│                                                                   │
│  3. Azure Blob Storage                                           │
│     ✅ Store master resumes                                      │
│     ✅ Version control for tailored resumes                      │
│     ✅ Secure access with SAS tokens                             │
│     💰 Cost: ~$0.018/GB/month                                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Benefits**:
- ✅ Scalable infrastructure
- ✅ Enterprise-grade security
- ✅ Seamless integration between services
- ✅ Pay-as-you-go pricing
- ✅ Managed services (no infrastructure management)

**Next Steps**:
1. Create Azure resources (see Setup Guide)
2. Configure `.env` with credentials
3. Test each integration separately
4. Monitor usage and costs
5. Optimize based on patterns

---

## Additional Resources

- **Azure OpenAI**: https://learn.microsoft.com/azure/ai-services/openai/
- **Azure AI Search**: https://learn.microsoft.com/azure/search/
- **Azure Blob Storage**: https://learn.microsoft.com/azure/storage/blobs/
- **Azure SDK for Python**: https://learn.microsoft.com/python/api/overview/azure/
- **Flash Service Code**: `app/services/flash/`
