"""
QA Agent
Specialized agent for question answering using LLM
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class QAAgent:
    """
    LLM-powered agent for answering application questions
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize QA agent
        
        Args:
            llm_client: Azure OpenAI client
        """
        self.llm_client = llm_client
        self.system_prompt = """
You are a professional job application assistant helping users answer application questions truthfully and effectively.

Your responsibilities:
1. Answer questions based only on provided context
2. Never fabricate information
3. Provide concise, professional answers
4. Maintain appropriate tone for job applications
5. Flag when information is insufficient

You must be honest and ethical in all responses.
"""
    
    async def answer_with_context(
        self,
        question: str,
        context: List[str],
        max_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Answer question using provided context
        
        Args:
            question: The question to answer
            context: List of context strings
            max_length: Maximum answer length in words
            
        Returns:
            {
                'answer': str,
                'confidence': float,
                'reasoning': str
            }
        """
        if not self.llm_client:
            return self._fallback_answer(question, context)
        
        context_text = '\n\n'.join(context)
        
        length_instruction = ""
        if max_length:
            length_instruction = f"\nKeep answer under {max_length} words."
        
        prompt = f"""
Question: {question}

Context:
{context_text}

Instructions:
- Answer based only on the provided context
- Be concise and professional
- If context is insufficient, say so{length_instruction}

Answer:
"""
        
        try:
            response = await self._call_llm(prompt)
            
            # Assess confidence based on context quality
            confidence = self._assess_confidence(question, context, response)
            
            return {
                'answer': response,
                'confidence': confidence,
                'reasoning': 'Generated from provided context'
            }
        except Exception as e:
            logger.error(f"QA failed: {e}")
            return self._fallback_answer(question, context)
    
    async def generate_multiple_answers(
        self,
        question: str,
        context: List[str],
        count: int = 3
    ) -> List[str]:
        """
        Generate multiple answer variations
        
        Args:
            question: The question
            context: Context strings
            count: Number of variations
            
        Returns:
            List of answer variations
        """
        if not self.llm_client:
            return [self._fallback_answer(question, context)['answer']]
        
        context_text = '\n\n'.join(context)
        
        prompt = f"""
Question: {question}

Context:
{context_text}

Generate {count} different professional ways to answer this question.
Each answer should be truthful and based on the context.
Separate answers with "---"

Answers:
"""
        
        try:
            response = await self._call_llm(prompt, temperature=0.7)
            answers = [a.strip() for a in response.split('---') if a.strip()]
            return answers[:count]
        except Exception as e:
            logger.error(f"Multiple answer generation failed: {e}")
            return [self._fallback_answer(question, context)['answer']]
    
    async def improve_answer(
        self,
        original_answer: str,
        question: str,
        feedback: str
    ) -> str:
        """
        Improve answer based on feedback
        
        Args:
            original_answer: Current answer
            question: Original question
            feedback: Improvement feedback
            
        Returns:
            Improved answer
        """
        if not self.llm_client:
            return original_answer
        
        prompt = f"""
Original Question: {question}

Current Answer: {original_answer}

Feedback: {feedback}

Provide an improved version of the answer that addresses the feedback while maintaining truthfulness.

Improved Answer:
"""
        
        try:
            improved = await self._call_llm(prompt)
            return improved
        except Exception as e:
            logger.error(f"Answer improvement failed: {e}")
            return original_answer
    
    async def extract_key_points(self, text: str, count: int = 5) -> List[str]:
        """
        Extract key points from text
        
        Args:
            text: Input text
            count: Number of key points
            
        Returns:
            List of key points
        """
        if not self.llm_client:
            return self._extract_keypoints_fallback(text, count)
        
        prompt = f"""
Extract the {count} most important key points from this text:

{text}

List key points, one per line:
"""
        
        try:
            response = await self._call_llm(prompt)
            points = [line.strip() for line in response.split('\n') if line.strip()]
            return points[:count]
        except Exception as e:
            logger.error(f"Key point extraction failed: {e}")
            return self._extract_keypoints_fallback(text, count)
    
    async def _call_llm(self, prompt: str, temperature: float = 0.4) -> str:
        """Call Azure OpenAI LLM"""
        if not self.llm_client:
            return ""
        
        # Placeholder for actual Azure OpenAI call
        # response = await self.llm_client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[
        #         {"role": "system", "content": self.system_prompt},
        #         {"role": "user", "content": prompt}
        #     ],
        #     temperature=temperature,
        #     max_tokens=500
        # )
        # return response.choices[0].message.content
        
        return ""
    
    def _assess_confidence(
        self,
        question: str,
        context: List[str],
        answer: str
    ) -> float:
        """Assess confidence in the answer"""
        
        # Simple heuristic
        if not context:
            return 0.3
        
        # Check if answer contains info from context
        answer_lower = answer.lower()
        context_text = ' '.join(context).lower()
        
        # Count word overlap
        answer_words = set(answer_lower.split())
        context_words = set(context_text.split())
        
        overlap = len(answer_words & context_words)
        overlap_ratio = overlap / len(answer_words) if answer_words else 0
        
        # Confidence based on overlap
        if overlap_ratio > 0.5:
            return 0.85
        elif overlap_ratio > 0.3:
            return 0.65
        else:
            return 0.45
    
    def _fallback_answer(
        self,
        question: str,
        context: List[str]
    ) -> Dict[str, Any]:
        """Fallback answer without LLM"""
        
        if context:
            # Use first context as answer
            answer = context[0][:200]  # Truncate if too long
            confidence = 0.6
        else:
            answer = "Information not available in provided context."
            confidence = 0.2
        
        return {
            'answer': answer,
            'confidence': confidence,
            'reasoning': 'Fallback mode - LLM unavailable'
        }
    
    def _extract_keypoints_fallback(self, text: str, count: int) -> List[str]:
        """Fallback key point extraction"""
        
        # Split into sentences
        sentences = text.split('.')
        
        # Take first N non-empty sentences
        points = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 20:
                points.append(sentence + '.')
                if len(points) >= count:
                    break
        
        return points
