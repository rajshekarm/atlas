# RAG (Retrieval-Augmented Generation) in Flash Service

## 📚 Table of Contents
1. [What is RAG?](#what-is-rag)
2. [Why RAG for Job Applications?](#why-rag-for-job-applications)
3. [Flash Service RAG Architecture](#flash-service-rag-architecture)
4. [Implementation Details](#implementation-details)
5. [Code Walkthrough](#code-walkthrough)
6. [Data Flow](#data-flow)
7. [Future Enhancements](#future-enhancements)

---

## What is RAG?

**RAG (Retrieval-Augmented Generation)** is an AI architecture pattern that combines:
- **Retrieval**: Searching through a knowledge base to find relevant information
- **Augmentation**: Adding retrieved context to LLM prompts
- **Generation**: Using LLM to generate answers based on retrieved context

### Traditional LLM vs RAG

```
Traditional LLM:
User Question → LLM → Answer (may hallucinate)

RAG:
User Question → Search Knowledge Base → Retrieve Context → LLM + Context → Answer (grounded in facts)
```

### Key Benefits
✅ **Reduces Hallucinations**: LLM answers based on real data, not imagination  
✅ **Always Up-to-Date**: Knowledge base can be updated without retraining the model  
✅ **Source Attribution**: Can cite where information came from  
✅ **Cost-Effective**: No need to fine-tune expensive models  

---

## Why RAG for Job Applications?

In the Flash service, RAG solves critical problems:

### Problem 1: Consistency Across Applications
**Without RAG**: User answers the same question differently each time  
**With RAG**: System retrieves past approved answers → consistent responses

### Problem 2: Truthfulness
**Without RAG**: LLM might fabricate experience or skills  
**With RAG**: LLM only uses information from resume + profile → truthful answers

### Problem 3: Personalization
**Without RAG**: Generic answers that don't match user's actual experience  
**With RAG**: Retrieves user-specific context → personalized, relevant answers

---

## Flash Service RAG Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUESTION ANSWERING FLOW                       │
└─────────────────────────────────────────────────────────────────┘

1. User Question
   │
   ├─→ "What programming languages do you know?"
   │
   ▼
2. Retrieval Phase (Multi-Source)
   │
   ├─→ SOURCE 1: User Profile (Structured Data)
   │   • Full name, email, skills list, experience years
   │   • High confidence (0.95) - direct match
   │
   ├─→ SOURCE 2: Resume Content (Document)
   │   • Parse resume sections
   │   • Find relevant paragraphs using keyword matching
   │   • Medium confidence (0.8)
   │
   ├─→ SOURCE 3: Past Approved Answers (Vector Database)
   │   • Convert question to embedding
   │   • Search similar past questions
   │   • Retrieve top K similar answers
   │   • Variable confidence based on similarity
   │
   ▼
3. Context Ranking
   │
   ├─→ Sort sources by relevance score
   ├─→ Take top 5 most relevant contexts
   │
   ▼
4. Prompt Augmentation
   │
   ├─→ Build LLM prompt:
   │   • System prompt (instructions)
   │   • Question
   │   • Retrieved contexts
   │   • User profile summary
   │
   ▼
5. LLM Generation
   │
   ├─→ Azure OpenAI (GPT-4)
   ├─→ Generate truthful answer
   ├─→ Calculate confidence score
   │
   ▼
6. Answer + Sources
   │
   └─→ Return:
       • Generated answer
       • Source attribution
       • Confidence score
       • Alternative answers (if low confidence)
```

---

## Implementation Details

### 1. **Multi-Source Retrieval**

Flash uses **3 retrieval sources** for comprehensive context:

#### Source 1: User Profile (Structured Data)
```python
# Direct field mapping
profile_mappings = {
    'name': user_profile.full_name,
    'email': user_profile.email,
    'phone': user_profile.phone,
    'skills': ', '.join(user_profile.skills),
    'experience': f"{user_profile.years_of_experience} years"
}
```
**Use Case**: Direct questions like "What is your email?" → instant, high-confidence answer

#### Source 2: Resume Content (Unstructured Text)
```python
# Semantic section matching
relevant_section = _find_relevant_section(question, resume_content)
```
**Use Case**: Essay questions like "Describe your experience with Python" → retrieves relevant resume paragraphs

#### Source 3: Past Approved Answers (Vector Database)
```python
# Vector similarity search
past_answers = vector_store.similarity_search(
    query=question,
    k=3  # Top 3 similar questions
)
```
**Use Case**: Similar questions user answered before → learn from past approvals

---

### 2. **Vector Database Options**

Flash supports multiple vector stores:

#### Option A: Azure AI Search (Recommended)
```python
from azure.search.documents import SearchClient
from azure.search.documents.models import Vector

# Store answer with embedding
await search_client.upload_documents([{
    'id': answer_id,
    'question': question,
    'answer': answer,
    'embedding': generate_embedding(question),
    'metadata': {...}
}])

# Search similar questions
results = search_client.search(
    search_text=None,
    vector=Vector(
        value=generate_embedding(user_question),
        k=3,
        fields="embedding"
    )
)
```

#### Option B: Chroma (Local Development)
```python
import chromadb

# Initialize
client = chromadb.PersistentClient(path="./data/knowledge_base")
collection = client.get_or_create_collection("approved_answers")

# Add answer
collection.add(
    documents=[answer],
    metadatas=[{'question': question, 'job_id': job_id}],
    ids=[answer_id]
)

# Search
results = collection.query(
    query_texts=[user_question],
    n_results=3
)
```

---

### 3. **Confidence Scoring**

Flash uses **multi-factor confidence scoring**:

```python
def calculate_confidence(sources, answer):
    factors = []
    
    # Factor 1: Source quality
    if sources and sources[0].relevance_score > 0.9:
        factors.append(0.95)  # High confidence from direct profile data
    
    # Factor 2: Source count
    source_count_score = min(len(sources) / 5, 1.0)
    factors.append(source_count_score)
    
    # Factor 3: Content overlap
    answer_words = set(answer.lower().split())
    source_words = set(' '.join(s.content for s in sources).lower().split())
    overlap = len(answer_words & source_words) / len(answer_words)
    factors.append(overlap)
    
    # Final confidence
    confidence = sum(factors) / len(factors)
    return confidence
```

**Confidence Levels**:
- **High (>0.8)**: Direct from profile, no review needed
- **Medium (0.5-0.8)**: From resume/past answers, light review
- **Low (<0.5)**: Insufficient context, requires human review

---

## Code Walkthrough

### File: `services/qa_engine.py`

#### Main Entry Point
```python
async def answer_question(
    self,
    context: QuestionContext,
    user_profile: UserProfile
) -> QuestionAnswer:
    """
    Answer application question using RAG
    """
    # Step 1: RETRIEVAL - Get relevant context
    retrieved_context = await self._retrieve_context(
        context.question,
        user_profile,
        context.resume_path
    )
    
    # Step 2: GENERATION - Create answer with LLM
    answer, confidence_score = await self._generate_answer(
        context,
        retrieved_context,
        user_profile
    )
    
    # Step 3: VALIDATION - Determine review requirements
    confidence = self._determine_confidence_level(confidence_score)
    requires_review = confidence == ConfidenceLevel.LOW
    
    return QuestionAnswer(...)
```

#### Retrieval Implementation
```python
async def _retrieve_context(
    self,
    question: str,
    user_profile: UserProfile,
    resume_path: Optional[str]
) -> List[AnswerSource]:
    """
    RAG Retrieval Phase - Multi-source context gathering
    """
    sources = []
    
    # SOURCE 1: Structured profile data
    profile_context = self._extract_from_profile(question, user_profile)
    if profile_context:
        sources.append(profile_context)  # High confidence (0.95)
    
    # SOURCE 2: Resume document
    if resume_path:
        resume_context = await self._extract_from_resume(question, resume_path)
        if resume_context:
            sources.append(resume_context)  # Medium confidence (0.8)
    
    # SOURCE 3: Vector database (past answers)
    if self.vector_store:
        past_answers = await self._search_past_answers(question)
        sources.extend(past_answers)  # Variable confidence
    
    # Rank by relevance
    sources.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return sources[:5]  # Top 5 most relevant
```

#### Generation with Context
```python
async def _generate_answer(
    self,
    context: QuestionContext,
    retrieved_sources: List[AnswerSource],
    user_profile: UserProfile
) -> tuple[str, float]:
    """
    RAG Generation Phase - Answer synthesis
    """
    # Short-circuit for high-confidence direct matches
    if retrieved_sources and retrieved_sources[0].relevance_score > 0.9:
        return retrieved_sources[0].content, retrieved_sources[0].relevance_score
    
    # Build augmented prompt
    prompt = f"""
You are helping a user fill out a job application. Answer truthfully based ONLY on the provided context.

QUESTION:
{context.question}

AVAILABLE CONTEXT:
"""
    
    # Add each source to prompt
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
3. Keep the answer concise and professional

ANSWER:
"""
    
    # Call LLM with augmented prompt
    answer = await self._call_llm(prompt)
    
    # Calculate confidence
    avg_relevance = sum(s.relevance_score for s in retrieved_sources) / len(retrieved_sources)
    confidence_score = min(avg_relevance, 0.85)
    
    return answer, confidence_score
```

---

## Data Flow

### Example: "What programming languages do you know?"

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: QUESTION INPUT                                           │
└─────────────────────────────────────────────────────────────────┘
Question: "What programming languages do you know?"
Field Type: text
Job ID: job_abc123
User ID: user_xyz789

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: RETRIEVAL                                                │
└─────────────────────────────────────────────────────────────────┘

SOURCE 1: User Profile
  Match: "programming" → skills field
  Retrieved: ["Python", "JavaScript", "TypeScript", "SQL"]
  Relevance: 0.95 (direct match)

SOURCE 2: Resume
  Section: "Technical Skills"
  Retrieved: "Languages: Python, JavaScript, TypeScript, SQL
              Proficient in Python with 5+ years experience..."
  Relevance: 0.85

SOURCE 3: Past Answers (Vector Search)
  Similar Question: "What languages are you proficient in?"
  Retrieved: "I'm proficient in Python, JavaScript, and SQL..."
  Relevance: 0.75
  
Ranked Sources: [Profile(0.95), Resume(0.85), PastAnswer(0.75)]

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: PROMPT AUGMENTATION                                      │
└─────────────────────────────────────────────────────────────────┘

Prompt to LLM:
"
You are helping fill a job application. Answer based on context:

QUESTION: What programming languages do you know?

CONTEXT:
1. From profile (0.95): Python, JavaScript, TypeScript, SQL
2. From resume (0.85): Languages: Python, JavaScript, TypeScript...
3. From past_answer (0.75): I'm proficient in Python, JavaScript...

USER PROFILE:
- Name: John Doe
- Experience: 5 years

Answer truthfully:
"

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: LLM GENERATION                                           │
└─────────────────────────────────────────────────────────────────┘

LLM Output:
"I am proficient in Python, JavaScript, TypeScript, and SQL. 
I have 5+ years of experience with Python, which is my primary language."

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: RESPONSE WITH METADATA                                   │
└─────────────────────────────────────────────────────────────────┘

{
  "answer": "I am proficient in Python, JavaScript, TypeScript, and SQL...",
  "confidence": "high",
  "confidence_score": 0.88,
  "sources": [
    {"source_type": "profile", "relevance_score": 0.95},
    {"source_type": "resume", "relevance_score": 0.85},
    {"source_type": "past_answer", "relevance_score": 0.75}
  ],
  "requires_review": false,
  "timestamp": "2026-02-01T10:30:00"
}
```

---

## Future Enhancements

### 1. **Advanced Embeddings**
Currently: Simple keyword matching for resume sections  
**Upgrade**: Use Azure OpenAI embeddings for semantic search

```python
# Generate embeddings
from openai import AzureOpenAI

def generate_embedding(text: str) -> List[float]:
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

# Store with embeddings
resume_chunks = chunk_resume(resume_content)
for chunk in resume_chunks:
    embedding = generate_embedding(chunk)
    vector_store.add(chunk, embedding, metadata={...})
```

### 2. **Hybrid Search**
Combine keyword search + vector search for best results

```python
# Keyword search (BM25)
keyword_results = search_index.search(question, top=5)

# Vector search (semantic)
vector_results = vector_store.search(embedding, top=5)

# Merge with reciprocal rank fusion
combined_results = merge_results(keyword_results, vector_results)
```

### 3. **Contextual Re-ranking**
Use a re-ranker model to improve relevance

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Score each candidate
scores = reranker.predict([
    (question, candidate.content) 
    for candidate in candidates
])

# Re-sort by reranker scores
reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
```

### 4. **Intelligent Chunking**
Better resume parsing with context preservation

```python
def smart_chunk_resume(resume: str) -> List[Chunk]:
    """
    Split resume into chunks while preserving context
    """
    chunks = []
    
    # Parse into sections
    sections = parse_sections(resume)
    
    for section in sections:
        # Keep section header with content
        for experience in section.experiences:
            chunk = Chunk(
                content=f"{section.header}\n{experience}",
                metadata={
                    'section': section.type,
                    'dates': extract_dates(experience),
                    'companies': extract_companies(experience)
                }
            )
            chunks.append(chunk)
    
    return chunks
```

### 5. **Query Expansion**
Improve retrieval by expanding user queries

```python
async def expand_query(question: str) -> List[str]:
    """
    Generate alternative phrasings of question
    """
    prompt = f"""
    Generate 3 alternative ways to ask this question:
    "{question}"
    """
    
    alternatives = await llm.generate(prompt)
    return [question] + alternatives

# Search with all variations
results = []
for query in expand_query(question):
    results.extend(vector_store.search(query))

# Deduplicate and rank
final_results = deduplicate(results)
```

---

## Performance Considerations

### Latency Optimization
```python
# Parallel retrieval
import asyncio

async def fast_retrieve(question, profile, resume_path):
    """
    Retrieve from multiple sources in parallel
    """
    tasks = [
        extract_from_profile(question, profile),
        extract_from_resume(question, resume_path),
        search_vector_db(question)
    ]
    
    results = await asyncio.gather(*tasks)
    return flatten(results)
```

### Caching Strategy
```python
from functools import lru_cache

# Cache embeddings
@lru_cache(maxsize=1000)
def get_embedding(text: str) -> List[float]:
    return generate_embedding(text)

# Cache search results (short TTL)
redis_client.setex(
    f"search:{question_hash}",
    ttl=300,  # 5 minutes
    value=json.dumps(results)
)
```

---

## Summary

**RAG in Flash Service** solves three critical problems:

1. **Truthfulness**: Grounds answers in user's actual resume and profile
2. **Consistency**: Learns from past approved answers
3. **Personalization**: Retrieves user-specific context for every answer

**Architecture**:
- Multi-source retrieval (profile + resume + past answers)
- Confidence-based validation
- Source attribution for transparency
- Fallback modes when context is insufficient

**Result**: AI that helps users apply to jobs faster while maintaining complete honesty and ethical standards. 🎯

---

## References

- Azure AI Search Documentation: https://learn.microsoft.com/azure/search/
- Azure OpenAI Embeddings: https://learn.microsoft.com/azure/ai-services/openai/concepts/understand-embeddings
- RAG Paper: https://arxiv.org/abs/2005.11401
- Flash Service Code: `app/services/flash/services/qa_engine.py`
