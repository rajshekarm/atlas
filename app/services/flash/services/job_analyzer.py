"""
Job Analyzer Service
Analyzes job descriptions using NLP + LLM to extract requirements
"""
from typing import List, Dict, Any
import hashlib
from datetime import datetime

from app.services.flash.models import (
    JobDescription, 
    JobAnalysis, 
    ConfidenceLevel
)


class JobAnalyzerService:
    """
    Analyzes job descriptions to extract key information
    """
    
    def __init__(self, llm_client=None):
        """Initialize with optional LLM client (Azure OpenAI)"""
        self.llm_client = llm_client
        
    def generate_job_id(self, job_description: JobDescription) -> str:
        """Generate unique job ID from URL and title"""
        content = f"{job_description.url}_{job_description.title}_{job_description.company or ''}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def analyze_job(self, job_description: JobDescription) -> JobAnalysis:
        """
        Analyze job description and extract structured information
        
        Args:
            job_description: Job description data
            
        Returns:
            JobAnalysis with extracted information
        """
        job_id = self.generate_job_id(job_description)
        
        # Extract skills using LLM
        required_skills = await self._extract_skills(
            job_description.requirements + [job_description.description]
        )
        preferred_skills = await self._extract_skills(
            job_description.preferred_qualifications
        )
        
        # Identify technologies
        technologies = await self._extract_technologies(job_description)
        
        # Determine seniority level
        seniority = self._determine_seniority(job_description)
        
        # Determine role focus
        role_focus = self._determine_role_focus(job_description)
        
        # Extract key requirements
        key_requirements = await self._extract_key_requirements(job_description)
        
        return JobAnalysis(
            job_id=job_id,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            technologies=technologies,
            seniority_level=seniority,
            role_focus=role_focus,
            key_requirements=key_requirements,
            timestamp=datetime.now()
        )
    
    async def _extract_skills(self, text_list: List[str]) -> List[str]:
        """Extract skills from text using LLM"""
        if not text_list:
            return []
            
        combined_text = " ".join(text_list)
        
        if self.llm_client:
            # Use LLM to extract skills
            prompt = f"""
            Extract technical and professional skills from the following job requirements.
            Return only the skill names, one per line.
            
            Requirements:
            {combined_text}
            
            Skills:
            """
            response = await self._call_llm(prompt)
            skills = [s.strip() for s in response.split('\n') if s.strip()]
            return skills[:20]  # Limit to top 20
        else:
            # Fallback: Simple keyword extraction
            return self._extract_skills_fallback(combined_text)
    
    async def _extract_technologies(self, job_description: JobDescription) -> List[str]:
        """Extract technology stack from job description"""
        all_text = f"{job_description.description} {' '.join(job_description.requirements)}"
        
        # Common tech keywords
        tech_keywords = [
            'python', 'javascript', 'typescript', 'java', 'c#', 'go', 'rust',
            'react', 'vue', 'angular', 'node.js', 'express', 'fastapi', 'django', 'flask',
            'postgresql', 'mongodb', 'redis', 'mysql', 'dynamodb',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'git', 'jenkins', 'github actions', 'ci/cd'
        ]
        
        found_tech = ["python"]
        all_text_lower = all_text.lower()
        
        for tech in tech_keywords:
            if tech in all_text_lower:
                found_tech.append(tech)
                
        return found_tech
    
    def _determine_seniority(self, job_description: JobDescription) -> str:
        """Determine seniority level from job title and requirements"""
        title_lower = job_description.title.lower()
        
        if any(word in title_lower for word in ['senior', 'sr', 'lead', 'principal', 'staff']):
            return 'senior'
        elif any(word in title_lower for word in ['junior', 'jr', 'entry', 'associate']):
            return 'junior'
        else:
            return 'mid'
    
    def _determine_role_focus(self, job_description: JobDescription) -> str:
        """Determine primary role focus"""
        title_lower = job_description.title.lower()
        desc_lower = job_description.description.lower()
        
        if 'full stack' in title_lower or 'fullstack' in title_lower:
            return 'full-stack'
        elif 'backend' in title_lower or 'back-end' in title_lower:
            return 'backend'
        elif 'frontend' in title_lower or 'front-end' in title_lower:
            return 'frontend'
        elif 'devops' in title_lower or 'sre' in title_lower:
            return 'devops'
        elif 'data' in title_lower or 'ml' in title_lower or 'ai' in title_lower:
            return 'data/ml'
        else:
            # Analyze description
            backend_score = desc_lower.count('backend') + desc_lower.count('api') + desc_lower.count('server')
            frontend_score = desc_lower.count('frontend') + desc_lower.count('ui') + desc_lower.count('react')
            
            if backend_score > frontend_score:
                return 'backend'
            elif frontend_score > backend_score:
                return 'frontend'
            else:
                return 'general'
    
    async def _extract_key_requirements(self, job_description: JobDescription) -> List[str]:
        """Extract top key requirements"""
        requirements = job_description.requirements[:10]  # Top 10
        return requirements
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM (Azure OpenAI) for text generation"""
        if not self.llm_client:
            return ""
        
        try:
            # Use the unified interface - works with any provider
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            return response
        except Exception as e:
            print(f"LLM call failed: {e}")
            return ""
    
    def _extract_skills_fallback(self, text: str) -> List[str]:
        """Fallback skill extraction without LLM"""
        common_skills = [
            'python', 'javascript', 'typescript', 'react', 'node.js',
            'sql', 'nosql', 'rest api', 'graphql', 'microservices',
            'docker', 'kubernetes', 'aws', 'azure', 'ci/cd',
            'git', 'agile', 'scrum', 'problem solving', 'communication'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
                
        return found_skills
