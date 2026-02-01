"""
Question Answering Service
RAG-based system to answer application questions using user profile and resume
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from app.services.flash.models import (
    QuestionContext,
    QuestionAnswer,
    AnswerSource,
    ConfidenceLevel,
    UserProfile
)


class QuestionAnsweringService:
    """
    RAG-powered service to answer application questions
    Uses Azure AI Search for vector retrieval
    """
    
    def __init__(
        self,
        llm_client=None,
        vector_store=None,
        knowledge_base_path: str = "./data/knowledge_base"
    ):
        """
        Initialize QA service
        
        Args:
            llm_client: Azure OpenAI client
            vector_store: Azure AI Search or Chroma client
            knowledge_base_path: Path to store past answers
        """
        self.llm_client = llm_client
        self.vector_store = vector_store
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        
        # Confidence thresholds
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.5,
            "low": 0.0
        }
    
    async def answer_question(
        self,
        context: QuestionContext,
        user_profile: UserProfile
    ) -> QuestionAnswer:
        """
        Answer application question using RAG
        
        Args:
            context: Question context including field info
            user_profile: User profile with structured data
            
        Returns:
            Answer with confidence score and sources
        """
        # Retrieve relevant context
        retrieved_context = await self._retrieve_context(
            context.question,
            user_profile,
            context.resume_path
        )
        
        # Generate answer using LLM
        answer, confidence_score = await self._generate_answer(
            context,
            retrieved_context,
            user_profile
        )
        
        # Determine confidence level
        confidence = self._determine_confidence_level(confidence_score)
        
        # Determine if review is required
        requires_review = (
            confidence == ConfidenceLevel.LOW or
            confidence_score < self.confidence_thresholds["medium"]
        )
        
        # Generate alternative answers if confidence is low
        alternative_answers = None
        if requires_review and self.llm_client:
            alternative_answers = await self._generate_alternatives(
                context,
                retrieved_context,
                user_profile
            )
        
        return QuestionAnswer(
            field_id=context.field_id,
            question=context.question,
            answer=answer,
            confidence=confidence,
            confidence_score=confidence_score,
            sources=retrieved_context,
            requires_review=requires_review,
            alternative_answers=alternative_answers,
            timestamp=datetime.now()
        )
    
    async def _retrieve_context(
        self,
        question: str,
        user_profile: UserProfile,
        resume_path: Optional[str]
    ) -> List[AnswerSource]:
        """
        Retrieve relevant context using RAG
        
        Sources:
        1. User profile (structured data)
        2. Resume content
        3. Past approved answers (vector database)
        """
        sources = []
        
        # Source 1: User Profile
        profile_context = self._extract_from_profile(question, user_profile)
        if profile_context:
            sources.append(profile_context)
        
        # Source 2: Resume
        if resume_path:
            resume_context = await self._extract_from_resume(question, resume_path)
            if resume_context:
                sources.append(resume_context)
        
        # Source 3: Past Answers (Vector Search)
        if self.vector_store:
            past_answers = await self._search_past_answers(question)
            sources.extend(past_answers)
        
        # Sort by relevance
        sources.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return sources[:5]  # Top 5 most relevant
    
    def _extract_from_profile(
        self,
        question: str,
        user_profile: UserProfile
    ) -> Optional[AnswerSource]:
        """Extract relevant information from user profile"""
        
        question_lower = question.lower()
        
        # Map common questions to profile fields
        profile_mappings = {
            'name': user_profile.full_name,
            'email': user_profile.email,
            'phone': user_profile.phone,
            'location': user_profile.location,
            'linkedin': user_profile.linkedin_url,
            'github': user_profile.github_url,
            'portfolio': user_profile.portfolio_url,
            'title': user_profile.current_title,
            'experience': f"{user_profile.years_of_experience} years",
            'skills': ', '.join(user_profile.skills),
            'authorization': user_profile.work_authorization,
        }
        
        # Check which profile field is relevant
        for key, value in profile_mappings.items():
            if key in question_lower and value:
                return AnswerSource(
                    source_type="profile",
                    content=str(value),
                    relevance_score=0.95  # High confidence for direct profile data
                )
        
        return None
    
    async def _extract_from_resume(
        self,
        question: str,
        resume_path: str
    ) -> Optional[AnswerSource]:
        """Extract relevant information from resume"""
        
        try:
            with open(resume_path, 'r', encoding='utf-8') as f:
                resume_content = f.read()
            
            # Use vector search or semantic matching to find relevant section
            relevant_section = self._find_relevant_section(
                question,
                resume_content
            )
            
            if relevant_section:
                return AnswerSource(
                    source_type="resume",
                    content=relevant_section,
                    relevance_score=0.8
                )
        except FileNotFoundError:
            pass
        
        return None
    
    def _find_relevant_section(
        self,
        question: str,
        resume_content: str
    ) -> Optional[str]:
        """Find most relevant section from resume (simple implementation)"""
        
        # Split resume into paragraphs
        paragraphs = [p.strip() for p in resume_content.split('\n\n') if p.strip()]
        
        # Simple keyword matching
        question_words = set(question.lower().split())
        
        best_match = None
        best_score = 0
        
        for para in paragraphs:
            para_words = set(para.lower().split())
            overlap = len(question_words & para_words)
            
            if overlap > best_score:
                best_score = overlap
                best_match = para
        
        return best_match if best_score > 2 else None
    
    async def _search_past_answers(
        self,
        question: str
    ) -> List[AnswerSource]:
        """Search past approved answers using vector database"""
        
        if not self.vector_store:
            return []
        
        # Placeholder for vector search
        # results = await self.vector_store.similarity_search(
        #     query=question,
        #     k=3
        # )
        
        # For now, return empty
        return []
    
    async def _generate_answer(
        self,
        context: QuestionContext,
        retrieved_sources: List[AnswerSource],
        user_profile: UserProfile
    ) -> tuple[str, float]:
        """
        Generate answer using LLM with retrieved context
        
        Returns:
            (answer, confidence_score)
        """
        
        # If we have high-confidence direct data, use it
        if retrieved_sources and retrieved_sources[0].relevance_score > 0.9:
            return retrieved_sources[0].content, retrieved_sources[0].relevance_score
        
        # Otherwise, use LLM to synthesize answer
        if self.llm_client and retrieved_sources:
            prompt = self._build_qa_prompt(context, retrieved_sources, user_profile)
            answer = await self._call_llm(prompt)
            
            # Calculate confidence based on source quality
            avg_relevance = sum(s.relevance_score for s in retrieved_sources) / len(retrieved_sources)
            confidence_score = min(avg_relevance, 0.85)  # Cap at 0.85 for LLM-generated
            
            return answer, confidence_score
        
        # Fallback: Use profile data directly
        if retrieved_sources:
            return retrieved_sources[0].content, 0.6
        
        return "Unable to answer this question with available information.", 0.2
    
    def _build_qa_prompt(
        self,
        context: QuestionContext,
        sources: List[AnswerSource],
        user_profile: UserProfile
    ) -> str:
        """Build LLM prompt for answering question"""
        
        prompt = f"""
You are helping a user fill out a job application. Answer the following question truthfully and professionally based only on the provided context.

QUESTION:
{context.question}

FIELD TYPE: {context.field_type}

AVAILABLE CONTEXT:
"""
        
        for i, source in enumerate(sources, 1):
            prompt += f"\n{i}. From {source.source_type} (relevance: {source.relevance_score:.2f}):\n{source.content}\n"
        
        prompt += f"""

USER PROFILE:
- Name: {user_profile.full_name}
- Current Title: {user_profile.current_title}
- Experience: {user_profile.years_of_experience} years
- Skills: {', '.join(user_profile.skills[:10])}

INSTRUCTIONS:
1. Answer truthfully based only on the provided context
2. Do not fabricate information
3. Keep the answer concise and professional
4. Match the tone expected for a job application
5. If the question asks for specific data (email, phone), provide it directly
6. If asking for an essay/explanation, provide 2-3 sentences

ANSWER:
"""
        return prompt
    
    async def _generate_alternatives(
        self,
        context: QuestionContext,
        sources: List[AnswerSource],
        user_profile: UserProfile
    ) -> List[str]:
        """Generate alternative answer options"""
        
        if not self.llm_client:
            return []
        
        # Generate 2-3 alternative phrasings
        prompt = f"""
Generate 3 alternative ways to answer this job application question:

QUESTION: {context.question}

CONTEXT:
{sources[0].content if sources else 'Limited context available'}

Provide 3 different professional answers, each on a new line.
"""
        
        response = await self._call_llm(prompt)
        alternatives = [line.strip() for line in response.split('\n') if line.strip()]
        
        return alternatives[:3]
    
    def _determine_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert numeric score to confidence level"""
        if score >= self.confidence_thresholds["high"]:
            return ConfidenceLevel.HIGH
        elif score >= self.confidence_thresholds["medium"]:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for text generation"""
        if not self.llm_client:
            return ""
        
        # Placeholder for Azure OpenAI call
        # response = await self.llm_client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=0.4,
        #     max_tokens=300
        # )
        # return response.choices[0].message.content
        
        return ""
    
    async def store_approved_answer(
        self,
        question: str,
        answer: str,
        metadata: Dict[str, Any]
    ):
        """
        Store approved answer in knowledge base for future use
        
        Args:
            question: The question that was asked
            answer: The approved answer
            metadata: Additional context (job_id, company, etc.)
        """
        if self.vector_store:
            # Store in vector database
            # await self.vector_store.add_documents([{
            #     'question': question,
            #     'answer': answer,
            #     'metadata': metadata,
            #     'timestamp': datetime.now().isoformat()
            # }])
            pass
        
        # Also store in local file
        log_file = self.knowledge_base_path / "approved_answers.jsonl"
        import json
        with open(log_file, 'a', encoding='utf-8') as f:
            entry = {
                'question': question,
                'answer': answer,
                'metadata': metadata,
                'timestamp': datetime.now().isoformat()
            }
            f.write(json.dumps(entry) + '\n')
