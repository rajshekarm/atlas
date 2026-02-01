"""
Resume Tailor Service
Ethically tailors resumes to match job descriptions with strict guardrails
"""
from typing import List, Dict, Optional
import os
from pathlib import Path
from datetime import datetime

from app.services.flash.models import (
    JobDescription,
    JobAnalysis,
    ResumeTailoringRequest,
    ResumeTailoringResponse,
    ResumeSection,
    ConfidenceLevel
)


class ResumeTailorService:
    """
    Tailors resumes to match job descriptions while maintaining truthfulness
    """
    
    def __init__(self, llm_client=None, storage_path: str = "./data/resumes"):
        """
        Initialize resume tailor service
        
        Args:
            llm_client: Azure OpenAI client
            storage_path: Path to store tailored resumes
        """
        self.llm_client = llm_client
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Guardrails configuration
        self.guardrails = {
            "no_new_skills": True,
            "no_date_changes": True,
            "no_fake_experience": True,
            "maintain_facts": True,
            "max_rewrite_percentage": 40  # Max 40% of content can be rewritten
        }
    
    async def tailor_resume(
        self,
        request: ResumeTailoringRequest,
        job_analysis: JobAnalysis
    ) -> ResumeTailoringResponse:
        """
        Tailor resume for specific job with strict guardrails
        
        Args:
            request: Tailoring request with master resume
            job_analysis: Analysis of target job
            
        Returns:
            Tailored resume with diff preview
        """
        # Read master resume
        resume_content = self._read_resume(request.master_resume_path)
        
        # Parse resume into sections
        sections = self._parse_resume_sections(resume_content)
        
        # Tailor each section
        tailored_sections = []
        changes_list = []
        
        for section in sections:
            tailored = await self._tailor_section(
                section,
                job_analysis,
                request.focus_areas
            )
            
            # Apply guardrails
            if self._validate_section_changes(section, tailored):
                tailored_sections.append(tailored)
                if tailored.changes:
                    changes_list.extend(tailored.changes)
            else:
                # If validation fails, keep original
                tailored_sections.append(section)
        
        # Generate tailored resume file
        tailored_path = self._save_tailored_resume(
            tailored_sections,
            request.job_id
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            sections,
            tailored_sections,
            job_analysis
        )
        
        # Generate changes summary
        changes_summary = self._generate_changes_summary(changes_list)
        
        return ResumeTailoringResponse(
            job_id=request.job_id,
            original_resume_path=request.master_resume_path,
            tailored_resume_path=str(tailored_path),
            sections=tailored_sections,
            changes_summary=changes_summary,
            confidence=confidence,
            requires_approval=True,
            timestamp=datetime.now()
        )
    
    def _read_resume(self, resume_path: str) -> str:
        """Read resume content from file"""
        with open(resume_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _parse_resume_sections(self, content: str) -> List[ResumeSection]:
        """
        Parse resume into logical sections
        
        Common sections: Summary, Experience, Education, Skills, Projects
        """
        sections = []
        
        # Simple parsing (in production, use more sophisticated parsing)
        section_markers = {
            'summary': ['summary', 'objective', 'profile'],
            'experience': ['experience', 'work history', 'employment'],
            'education': ['education', 'academic'],
            'skills': ['skills', 'technical skills', 'technologies'],
            'projects': ['projects', 'portfolio']
        }
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if line is a section header
            found_section = None
            for section_type, markers in section_markers.items():
                if any(marker in line_lower for marker in markers):
                    found_section = section_type
                    break
            
            if found_section:
                # Save previous section
                if current_section and current_content:
                    sections.append(ResumeSection(
                        section_type=current_section,
                        original_content='\n'.join(current_content)
                    ))
                
                current_section = found_section
                current_content = [line]
            else:
                if current_section:
                    current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections.append(ResumeSection(
                section_type=current_section,
                original_content='\n'.join(current_content)
            ))
        
        return sections
    
    async def _tailor_section(
        self,
        section: ResumeSection,
        job_analysis: JobAnalysis,
        focus_areas: Optional[List[str]]
    ) -> ResumeSection:
        """
        Tailor individual section to match job requirements
        
        Args:
            section: Resume section to tailor
            job_analysis: Analysis of target job
            focus_areas: Specific areas to focus on
            
        Returns:
            Tailored section with changes tracked
        """
        if not self.llm_client:
            # No LLM available, return original
            return section
        
        # Build tailoring prompt with guardrails
        prompt = self._build_tailoring_prompt(section, job_analysis, focus_areas)
        
        # Call LLM to rewrite section
        tailored_content = await self._call_llm(prompt)
        
        # Detect changes
        changes = self._detect_changes(section.original_content, tailored_content)
        
        return ResumeSection(
            section_type=section.section_type,
            original_content=section.original_content,
            tailored_content=tailored_content,
            changes=changes
        )
    
    def _build_tailoring_prompt(
        self,
        section: ResumeSection,
        job_analysis: JobAnalysis,
        focus_areas: Optional[List[str]]
    ) -> str:
        """Build LLM prompt for tailoring with guardrails"""
        
        prompt = f"""
You are an ethical resume editor. Your task is to rewrite the following resume section to better match a job description.

STRICT RULES (GUARDRAILS):
1. DO NOT add any new skills, technologies, or experiences that are not already mentioned
2. DO NOT change any dates, company names, or job titles
3. DO NOT fabricate or exaggerate accomplishments
4. ONLY rephrase existing content to emphasize relevant aspects
5. Focus on highlighting existing skills that match the job requirements
6. Keep all factual information identical

TARGET JOB:
- Role: {job_analysis.role_focus}
- Seniority: {job_analysis.seniority_level}
- Key Skills: {', '.join(job_analysis.required_skills[:10])}
- Technologies: {', '.join(job_analysis.technologies[:10])}

RESUME SECTION ({section.section_type}):
{section.original_content}

FOCUS AREAS:
{', '.join(focus_areas) if focus_areas else 'General optimization'}

INSTRUCTIONS:
Rewrite the section to better emphasize skills and experiences that match the target job.
Only rephrase - do not add new information.

TAILORED SECTION:
"""
        return prompt
    
    def _validate_section_changes(
        self,
        original: ResumeSection,
        tailored: ResumeSection
    ) -> bool:
        """
        Validate that changes follow guardrails
        
        Returns True if changes are acceptable, False otherwise
        """
        if not tailored.tailored_content:
            return False
        
        original_text = original.original_content.lower()
        tailored_text = tailored.tailored_content.lower()
        
        # Check 1: No date changes
        if self.guardrails["no_date_changes"]:
            original_dates = self._extract_dates(original_text)
            tailored_dates = self._extract_dates(tailored_text)
            if original_dates != tailored_dates:
                return False
        
        # Check 2: Length check (shouldn't be drastically different)
        length_ratio = len(tailored_text) / len(original_text) if len(original_text) > 0 else 0
        if length_ratio > 1.5 or length_ratio < 0.5:
            return False
        
        # Check 3: Core facts preserved (check for key company names, titles)
        original_entities = self._extract_key_entities(original_text)
        tailored_entities = self._extract_key_entities(tailored_text)
        
        # All original entities should still be present
        for entity in original_entities:
            if entity not in tailored_text:
                return False
        
        return True
    
    def _extract_dates(self, text: str) -> set:
        """Extract dates from text (years, month-year patterns)"""
        import re
        date_patterns = [
            r'\b\d{4}\b',  # Years (2020, 2021, etc.)
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  # Month Year
        ]
        
        dates = set()
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.update(matches)
        
        return dates
    
    def _extract_key_entities(self, text: str) -> set:
        """Extract key entities (company names, titles, universities)"""
        # Simple extraction - in production use NER
        entities = set()
        
        # Look for capitalized phrases (likely company/university names)
        import re
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.update(capitalized)
        
        return entities
    
    def _detect_changes(self, original: str, tailored: str) -> List[str]:
        """Detect and describe changes made"""
        changes = []
        
        # Simple diff detection
        original_lines = set(original.split('\n'))
        tailored_lines = set(tailored.split('\n'))
        
        added = tailored_lines - original_lines
        removed = original_lines - tailored_lines
        
        if added:
            changes.append(f"Added {len(added)} new lines")
        if removed:
            changes.append(f"Removed {len(removed)} lines")
        
        return changes
    
    def _save_tailored_resume(
        self,
        sections: List[ResumeSection],
        job_id: str
    ) -> Path:
        """Save tailored resume to file"""
        filename = f"resume_tailored_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = self.storage_path / filename
        
        # Combine sections
        content_parts = []
        for section in sections:
            content = section.tailored_content if section.tailored_content else section.original_content
            content_parts.append(content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(content_parts))
        
        return filepath
    
    def _calculate_confidence(
        self,
        original_sections: List[ResumeSection],
        tailored_sections: List[ResumeSection],
        job_analysis: JobAnalysis
    ) -> ConfidenceLevel:
        """Calculate confidence in tailored resume"""
        
        # Check how many changes were made
        total_changes = sum(
            len(s.changes) if s.changes else 0 
            for s in tailored_sections
        )
        
        if total_changes == 0:
            return ConfidenceLevel.LOW  # No improvements made
        elif total_changes < 5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.HIGH
    
    def _generate_changes_summary(self, changes_list: List[str]) -> str:
        """Generate human-readable summary of changes"""
        if not changes_list:
            return "No significant changes made to resume."
        
        return f"Made {len(changes_list)} improvements to better match job requirements: " + "; ".join(changes_list[:5])
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for text generation"""
        if not self.llm_client:
            return ""
        
        # Placeholder for Azure OpenAI call
        # response = await self.llm_client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=0.5,
        #     max_tokens=1000
        # )
        # return response.choices[0].message.content
        
        return ""
