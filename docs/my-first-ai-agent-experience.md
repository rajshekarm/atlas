# My First Experience Developing an AI Assistant (AI Agent)

**Date**: February 2026  
**Project**: Flash - AI Job Application Assistant  
**Platform**: Atlas Backend

---

## The Beginning: A Problem Worth Solving

Like many job seekers, I found myself repeatedly filling out the same application forms, tailoring my resume for each position, and answering similar questions over and over. The process was tedious, time-consuming, and honestly, a bit soul-crushing.

Then I thought: *What if AI could help with this?*

Not in a "fake your experience" kind of way, but genuinely helping to present existing skills more effectively and streamlining the repetitive parts. That's when I decided to build **Flash** - my first real AI agent system.

---

## The Vision: What I Wanted to Build

I envisioned an AI assistant that could:
- **Analyze job descriptions** and extract key requirements
- **Tailor resumes** ethically (just better presentation)
- **Answer application questions** using my real profile and experience
- **Work with a Chrome Extension** to auto-fill forms in real browsers
- **Keep me in control** - human approval before anything gets submitted

The key word here: **ethical**. I didn't want to build something that would lie or fabricate experience. Just a smart assistant that helps me present my authentic self more effectively.

---

## Design Phase: Learning What "Agent" Really Means

Before diving into code, I had to understand: **What even is an AI agent?**

I spent days reading about:
- **LangChain** and tool-using agents
- **AutoGen** and multi-agent systems
- **OpenAI Assistants** API
- Traditional chatbots vs. autonomous agents

### The Confusion

The AI world uses "agent" to mean different things:
- Some say agents need **memory** and **conversation history**
- Others say agents must use **tools** and **external APIs**
- Some frameworks focus on **multi-agent collaboration**
- Others emphasize **autonomous goal-seeking**

I was overwhelmed. Do I need all of this?

### The Clarity

After prototyping, I realized: **I don't need full autonomy**. 

What I needed were **specialized reasoning modules** with clear purposes:
- A **Resume Agent** - expert at analyzing and improving resumes
- A **QA Agent** - expert at answering application questions truthfully

Not full autonomous agents, but **LLM-powered components with defined expertise**.

---

## Architecture Decision: Agents vs Services

This was my biggest learning moment. I discovered two layers were needed:

### **Agents = Reasoning**
```python
class ResumeAgent:
    """I am an expert resume consultant"""
    
    def analyze_resume_quality(self, resume):
        # Uses LLM to reason about quality
        # Returns: score, strengths, weaknesses
    
    def suggest_improvements(self, section, job_requirements):
        # Uses LLM to suggest ethical changes
        # Returns: specific improvement suggestions
```

**What agents do**:
- Have a defined **persona** (system prompt)
- Use **LLM to reason** about problems
- Return **insights and recommendations**
- Stay **stateless** (no memory between calls)

### **Services = Orchestration**
```python
class ResumeTailorService:
    """I orchestrate the resume tailoring workflow"""
    
    def tailor_resume(self, resume, job_description):
        # 1. Use ResumeAgent to analyze
        analysis = await self.resume_agent.analyze_resume_quality(resume)
        
        # 2. Apply business logic
        changes = self._generate_changes(analysis, job_description)
        
        # 3. Validate with guardrails
        validation = self.guardrails.validate_resume_changes(changes)
        
        # 4. Return result for user approval
        return tailored_resume
```

**What services do**:
- **Orchestrate** multiple steps
- **Call agents** for reasoning
- Apply **business logic and rules**
- Handle **data persistence**
- Manage **validation and errors**

### The Pattern

```
API Endpoint (Router)
    ↓
Service (Orchestration + Business Logic)
    ↓
Agent (LLM-Powered Reasoning)
    ↓
LLM (Azure OpenAI)
```

This separation made everything cleaner. Agents reason, services orchestrate.

---

## Building the Agents: System Prompts Are Everything

### Resume Agent

The first thing I learned: **the system prompt IS the agent's identity**.

```python
self.system_prompt = """
You are an expert resume consultant with years of experience.

Your responsibilities:
1. Analyze resumes for strengths and weaknesses
2. Suggest improvements to better match job descriptions
3. Ensure all changes are ethical and truthful
4. Never add fake experience or skills
5. Focus on emphasizing existing relevant experience

You must maintain the highest ethical standards.
"""
```

This prompt became the **moral compass** of my agent. Every suggestion it made was filtered through these constraints.

### QA Agent

For the question-answering agent, I needed different characteristics:

```python
self.system_prompt = """
You are a professional job application assistant.

Your responsibilities:
1. Answer questions based only on provided context
2. Never fabricate information
3. Provide concise, professional answers
4. Maintain appropriate tone for job applications
5. Flag when information is insufficient

You must be honest and ethical in all responses.
"""
```

### The Magic of Context

What made the QA agent powerful wasn't just the LLM - it was the **Retrieval-Augmented Generation (RAG)** approach:

```python
async def answer_question(self, question, user_profile):
    # 1. Retrieve relevant context
    context = await self._retrieve_context(
        question,
        user_profile,
        resume_path
    )
    
    # 2. Generate answer using LLM + context
    answer = await self.qa_agent.answer_with_context(
        question=question,
        context=context
    )
    
    # 3. Assess confidence
    # 4. Return answer with sources
```

The agent doesn't just guess - it searches my profile, resume, and past answers first.

---

## The Ethics Layer: Guardrails

Building AI that touches job applications felt like a huge responsibility. I didn't want to create something that could help people lie.

So I built a **Guardrails Service** with strict checks:

### Resume Tailoring Guardrails
```python
✅ Allowed:
- Rephrasing bullet points
- Emphasizing relevant skills
- Reordering sections
- Adjusting summary

❌ Blocked:
- Adding new skills not in original
- Changing dates or timelines
- Fabricating job titles
- Adding fake certifications
```

### Answer Validation
```python
def validate_answer(self, answer, user_profile):
    checks = [
        self._check_factual_consistency(answer, profile),
        self._check_no_fabrication(answer, profile),
        self._check_professional_tone(answer),
        self._check_length_appropriate(answer)
    ]
    return ValidationResult(checks)
```

Every AI-generated output goes through validation before reaching the user.

---

## The Reality Check: Database Requirements

About halfway through development, I had a realization moment.

I was writing code like this:

```python
@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str):
    # Placeholder
    return UserProfile(
        user_id=user_id,
        full_name="John Doe",  # 🤔 Wait...
        email="john@example.com",  # 🤔 This is hardcoded...
        skills=["Python", "FastAPI"]  # 🤔 Where's the real data?
    )
```

And comments like:
```python
# user_profile = fetch_user_profile(request.user_id)  # TODO: Implement
```

**The truth hit me**: I built an impressive AI system, but it had **no memory**.

Without a database:
- User profiles disappear after each request
- No application history
- RAG can't learn from past answers
- No analytics or tracking

I documented this realization in a [TODO.md](../app/services/flash/TODO.md) file - a humbling checklist of what still needs to be built.

### What Needs Persistence

1. **User Profiles** - Personal info, skills, experience
2. **Application History** - Track submissions and outcomes
3. **Vector Store** - Embeddings for RAG similarity search
4. **Job Analyses** - Cache analyzed job descriptions
5. **Approved Answers** - Learn from user corrections

**The plan**: Start with SQLite + FAISS, migrate to PostgreSQL + pgvector for production.

---

## Technical Stack: What Worked

### What I Used
- **FastAPI** - Clean, async, great for AI workloads
- **Pydantic** - Type safety saved me so many bugs
- **Azure OpenAI** - GPT-4 for agent reasoning
- **Modular Services** - Each service owns its domain

### What I Loved
1. **Async/Await** - Perfect for LLM calls (they're slow!)
2. **Pydantic Models** - 40+ models, zero serialization bugs
3. **Service Pattern** - Clear separation of concerns
4. **Fallback Logic** - Agents work even without LLM (degraded mode)

### What I'd Change
1. **Start with database** - Should've done this from day one
2. **Add observability** - Log LLM calls, latency, costs
3. **Token counting** - Track OpenAI usage to avoid surprises
4. **Rate limiting** - Need to protect against abuse

---

## Challenges & Lessons Learned

### Challenge 1: LLM Unpredictability
**Problem**: LLM sometimes returns malformed JSON  
**Solution**: Always validate outputs, have fallback parsers

### Challenge 2: Cost Anxiety
**Problem**: Every LLM call costs money  
**Solution**: 
- Cache job analyses (don't re-analyze same job)
- Use lower temperature (0.3-0.4) for consistent outputs
- Implement fallbacks for non-critical features

### Challenge 3: Latency
**Problem**: LLM calls take 2-5 seconds  
**Solution**:
- Run independent operations in parallel
- Show progress indicators to users
- Cache frequently accessed data

### Challenge 4: Ethical Boundaries
**Problem**: How to prevent misuse?  
**Solution**:
- Guardrails on all AI outputs
- User approval required before submission
- Confidence scores for transparency
- No CAPTCHA bypass, no automated clicking

---

## The Code Structure: What I Built

```
flash/
├── router.py              # 9 API endpoints
├── models.py              # 40+ Pydantic models
├── agents.py              # Agent orchestrator
├── config.py              # Configuration
├── services/
│   ├── job_analyzer.py    # Job description analysis (300+ lines)
│   ├── resume_tailor.py   # Resume tailoring (350+ lines)
│   ├── qa_engine.py       # RAG Q&A system (400+ lines)
│   └── guardrails.py      # Validation (450+ lines)
├── agents/
│   ├── resume_agent.py    # Resume expert (200+ lines)
│   └── qa_agent.py        # Q&A expert (295+ lines)
└── tests/
    └── test_flash.py      # API tests
```

**Total**: ~3,500 lines of code, 25+ files

---

## What I'm Proud Of

### 1. Ethical Design
Every decision prioritized honesty:
- Resume guardrails prevent fake experience
- QA agent admits when it doesn't know
- Human approval required before submission
- Confidence scores for transparency

### 2. Clean Architecture
Services, agents, and routers have clear responsibilities. Adding new features is straightforward.

### 3. Graceful Degradation
Even without LLM, the system provides basic functionality through rule-based fallbacks.

### 4. Real-World Ready
Not just a proof-of-concept - designed to integrate with Chrome Extension and handle real applications.

---

## What I Learned About AI Agents

### Agents Don't Need to Be Complex

I started thinking I needed:
- ❌ Multi-agent frameworks
- ❌ Tool-using capabilities  
- ❌ Memory and conversation history
- ❌ Autonomous goal-seeking

What I actually needed:
- ✅ Clear system prompts (agent identity)
- ✅ Focused reasoning tasks
- ✅ Context from RAG (not memory)
- ✅ Human-in-the-loop validation

**Lesson**: Start simple. Add complexity only when needed.

### System Prompts Are Underrated

The quality of my agents came down to **prompt engineering**:
- Define clear responsibilities
- Set ethical boundaries
- Specify output format
- Provide examples

A well-crafted system prompt is worth 1,000 lines of validation code.

### Agents vs Services Matter

Mixing reasoning (agent) with orchestration (service) creates spaghetti code. Keeping them separate made everything testable and maintainable.

---

## What's Next: The Roadmap

### Phase 1: Database (Critical)
- [ ] Implement SQLite for user profiles
- [ ] Add FAISS for vector search
- [ ] Migrate placeholder code to real DB calls
- [ ] Test RAG with actual embeddings

### Phase 2: Chrome Extension
- [ ] Build extension UI
- [ ] Connect to Flash API
- [ ] Implement form detection
- [ ] Add auto-fill with review

### Phase 3: Learning & Improvement
- [ ] Learn from user edits (feedback loop)
- [ ] Improve confidence scoring
- [ ] Add analytics dashboard
- [ ] A/B test different prompts

### Phase 4: Production
- [ ] Migrate to PostgreSQL + pgvector
- [ ] Add authentication
- [ ] Deploy to Azure
- [ ] Monitor costs and latency

---

## Reflections: Was It Worth It?

**Absolutely.**

### What I Gained

**Technical Skills**:
- LLM integration (Azure OpenAI)
- RAG architecture design
- Async Python patterns
- Agent-based system design

**Conceptual Understanding**:
- What makes something an "agent"
- When to use LLMs vs. rules
- Importance of guardrails
- RAG > Fine-tuning for personal data

**Product Thinking**:
- Ethics in AI products
- User control and transparency
- Graceful degradation
- Real-world constraints (cost, latency)

### What Surprised Me

1. **System prompts matter more than model choice** - GPT-3.5 with great prompts > GPT-4 with poor prompts
2. **Validation is 50% of the code** - Guardrails, checks, fallbacks everywhere
3. **Agents are simpler than I thought** - No need for complex frameworks
4. **Database planning should come first** - I learned this the hard way

---

## Advice for Your First AI Agent

If you're building your first AI agent/assistant, here's what I'd recommend:

### Start Simple
1. **Pick one narrow task** - Don't try to build AGI
2. **Define the agent's role clearly** - Write the system prompt first
3. **Build services around agents** - Separation of concerns matters

### Design for Ethics
1. **Think about misuse** - How could this be abused?
2. **Add guardrails early** - Don't bolt them on later
3. **Keep humans in the loop** - Especially for high-stakes decisions
4. **Be transparent** - Show confidence scores, sources

### Technical Foundations
1. **Plan for persistence** - You'll need a database
2. **Use RAG over fine-tuning** - Easier to update, more transparent
3. **Build fallbacks** - LLMs fail, APIs timeout
4. **Monitor everything** - Costs, latency, errors

### Iterate
1. **Ship something broken** - Perfect is the enemy of done
2. **Get real user feedback** - Your assumptions are wrong
3. **Measure what matters** - User satisfaction > technical metrics
4. **Document learnings** - Future you will thank present you

---

## The Real Lesson

Building an AI agent isn't about using the fanciest model or the latest framework.

It's about:
- **Solving a real problem** thoughtfully
- **Designing constraints** that prevent harm
- **Separating concerns** for maintainability
- **Planning infrastructure** (like databases!) upfront
- **Iterating based on reality**, not hype

My Flash assistant isn't perfect. It has placeholders, incomplete features, and a database that doesn't exist yet. But it taught me more about AI systems than any tutorial could.

---

## Resources That Helped Me

### Documentation
- [FastAPI Async Programming](https://fastapi.tiangolo.com/async/)
- [Azure OpenAI Best Practices](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Pydantic V2 Migration](https://docs.pydantic.dev/latest/)

### Concepts
- RAG (Retrieval-Augmented Generation)
- Few-shot prompting
- System prompt engineering
- Confidence scoring heuristics

### Inspiration
- Reading other developers' experiences with AI agents
- Ethical AI guidelines from OpenAI, Anthropic
- Real-world AI product postmortems

---

## Closing Thoughts

Six months ago, I didn't know what an AI agent was. Now I've built one (well, two agents in a system).

It's not deployed yet. The database is still on the TODO list. The Chrome Extension doesn't exist. But the foundation is solid, the architecture is clean, and the ethics are baked in.

**Most importantly**: I understand AI agents now. Not from reading about them, but from building one, making mistakes, learning, and iterating.

If you're thinking about building your first AI agent - just start. Pick a problem you face personally. Build something imperfect. Learn as you go.

The best way to understand AI agents is to build one.

---

**Project**: [Flash Service on GitHub](../app/services/flash/)  
**Documentation**: [Flash README](../app/services/flash/README.md)  
**TODO**: [Database Implementation Checklist](../app/services/flash/TODO.md)

*Written after building Flash AI Job Application Assistant on the Atlas platform.*

---

**P.S.** If you're building something similar, I'd love to hear about it. What worked? What didn't? What surprised you? The AI community learns by sharing experiences like these.

**P.P.S.** Yes, I still need to implement that database. It's on the TODO list. Right after I finish documenting everything. 😅
