"""
Resume Agent
Specialized agent for resume-related operations using LLM
"""
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ResumeAgent:
    """
    LLM-powered agent for resume analysis and tailoring
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize resume agent
        
        Args:
            llm_client: Azure OpenAI client
        """
        self.llm_client = llm_client
        self.system_prompt = """
You are an expert resume consultant with years of experience helping job seekers optimize their resumes.

Your responsibilities:
1. Analyze resumes for strengths and weaknesses
2. Suggest improvements to better match job descriptions
3. Ensure all changes are ethical and truthful
4. Never add fake experience or skills
5. Focus on emphasizing existing relevant experience

You must maintain the highest ethical standards and ensure all information is accurate.
"""
    
    async def analyze_resume_quality(self, resume_content: str) -> Dict[str, Any]:
        """
        Analyze resume quality and provide feedback
        
        Returns:
            {
                'overall_score': float,
                'strengths': List[str],
                'weaknesses': List[str],
                'suggestions': List[str]
            }
        """
        if not self.llm_client:
            return self._fallback_analysis(resume_content)
        
        prompt = f"""
Analyze the following resume and provide:
1. Overall quality score (0-100)
2. Top 3 strengths
3. Top 3 weaknesses
4. Top 3 improvement suggestions

Resume:
{resume_content}

Provide your analysis in JSON format.
"""
        
        try:
            response = await self._call_llm(prompt)
            # Parse response
            # analysis = json.loads(response)
            # return analysis
            
            return self._fallback_analysis(resume_content)
        except Exception as e:
            logger.error(f"Resume analysis failed: {e}")
            return self._fallback_analysis(resume_content)
    
    async def suggest_improvements(
        self,
        resume_section: str,
        job_requirements: str
    ) -> str:
        """
        Suggest specific improvements to a resume section
        
        Args:
            resume_section: Current section content
            job_requirements: Target job requirements
            
        Returns:
            Suggested improvements as text
        """
        if not self.llm_client:
            return "Consider emphasizing skills that match the job requirements."
        
        prompt = f"""
Given this resume section:
{resume_section}

And these job requirements:
{job_requirements}

Suggest specific, ethical improvements to better highlight relevant experience.
Do NOT suggest adding fake experience or skills.
Focus on better phrasing and emphasis.

Suggestions:
"""
        
        try:
            suggestions = await self._call_llm(prompt)
            return suggestions
        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            return "Unable to generate suggestions at this time."
    
    async def extract_key_achievements(self, resume_content: str) -> list:
        """
        Extract key achievements from resume
        
        Returns:
            List of achievement strings
        """
        if not self.llm_client:
            return self._extract_achievements_fallback(resume_content)
        
        prompt = f"""
Extract the top 5 key achievements from this resume.
Focus on quantifiable results and impact.

Resume:
{resume_content}

List achievements, one per line:
"""
        
        try:
            response = await self._call_llm(prompt)
            achievements = [line.strip() for line in response.split('\n') if line.strip()]
            return achievements[:5]
        except Exception as e:
            logger.error(f"Achievement extraction failed: {e}")
            return self._extract_achievements_fallback(resume_content)
    
    async def _call_llm(self, prompt: str, temperature: float = 0.3) -> str:
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
        #     max_tokens=1000
        # )
        # return response.choices[0].message.content
        
        return ""
    
    def _fallback_analysis(self, resume_content: str) -> Dict[str, Any]:
        """Fallback analysis without LLM"""
        word_count = len(resume_content.split())
        
        return {
            'overall_score': 70.0,
            'strengths': [
                'Resume contains relevant experience',
                'Appropriate length',
                'Clear structure'
            ],
            'weaknesses': [
                'Could emphasize more quantifiable achievements',
                'Some sections could be more concise',
                'Consider adding more technical keywords'
            ],
            'suggestions': [
                'Add metrics and numbers to achievements',
                'Tailor content to match job requirements',
                'Use action verbs to start bullet points'
            ]
        }
    
    def _extract_achievements_fallback(self, resume_content: str) -> list:
        """Fallback achievement extraction"""
        # Simple heuristic: look for lines with numbers
        lines = resume_content.split('\n')
        achievements = []
        
        for line in lines:
            if any(char.isdigit() for char in line) and len(line) > 20:
                achievements.append(line.strip())
                if len(achievements) >= 5:
                    break
        
        return achievements
