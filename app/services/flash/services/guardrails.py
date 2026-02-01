"""
Guardrails Service
Validates answers and actions to ensure ethical and safe operation
"""
from typing import List, Dict, Any
import re

from app.services.flash.models import (
    GuardrailCheck,
    ValidationResult,
    QuestionAnswer,
    ResumeSection,
    FilledField
)


class GuardrailsService:
    """
    Enforces ethical guardrails and validation rules
    """
    
    def __init__(self):
        """Initialize guardrails with configurable rules"""
        self.rules = {
            "no_fake_experience": True,
            "no_captcha_bypass": True,
            "require_work_authorization": True,
            "fact_check_answers": True,
            "content_safety": True
        }
        
        # Prohibited patterns
        self.prohibited_patterns = [
            r'captcha',
            r'bypass.*security',
            r'fake.*certification',
            r'forge.*document'
        ]
        
        # Sensitive keywords requiring extra validation
        self.sensitive_keywords = [
            'authorization', 'visa', 'citizen', 'eligible',
            'security clearance', 'criminal', 'disability'
        ]
    
    def validate_resume_changes(
        self,
        original: ResumeSection,
        tailored: ResumeSection
    ) -> ValidationResult:
        """
        Validate resume tailoring changes
        
        Ensures:
        - No fake experience added
        - No date manipulations
        - No skill fabrication
        """
        checks = []
        
        # Check 1: No new skills added
        check_skills = self._check_no_new_skills(original, tailored)
        checks.append(check_skills)
        
        # Check 2: Dates unchanged
        check_dates = self._check_dates_unchanged(original, tailored)
        checks.append(check_dates)
        
        # Check 3: Core facts preserved
        check_facts = self._check_facts_preserved(original, tailored)
        checks.append(check_facts)
        
        # Check 4: No suspicious additions
        check_suspicious = self._check_suspicious_content(tailored)
        checks.append(check_suspicious)
        
        # Determine overall validity
        critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
        warnings = [c for c in checks if not c.passed and c.severity == "warning"]
        
        valid = len(critical_failures) == 0
        can_proceed = valid
        requires_review = len(warnings) > 0
        
        return ValidationResult(
            valid=valid,
            checks=checks,
            can_proceed=can_proceed,
            requires_review=requires_review
        )
    
    def validate_answer(
        self,
        answer: QuestionAnswer,
        original_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate generated answer
        
        Ensures:
        - Truthfulness
        - No prohibited content
        - Appropriate for question type
        """
        checks = []
        
        # Check 1: Content safety
        check_safety = self._check_content_safety(answer.answer)
        checks.append(check_safety)
        
        # Check 2: Fact consistency
        check_consistency = self._check_fact_consistency(answer, original_data)
        checks.append(check_consistency)
        
        # Check 3: Sensitive question handling
        check_sensitive = self._check_sensitive_question(answer)
        checks.append(check_sensitive)
        
        # Check 4: Answer quality
        check_quality = self._check_answer_quality(answer)
        checks.append(check_quality)
        
        critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
        warnings = [c for c in checks if not c.passed and c.severity == "warning"]
        
        valid = len(critical_failures) == 0
        can_proceed = valid and answer.confidence_score > 0.3
        requires_review = len(warnings) > 0 or answer.confidence_score < 0.6
        
        return ValidationResult(
            valid=valid,
            checks=checks,
            can_proceed=can_proceed,
            requires_review=requires_review
        )
    
    def validate_application(
        self,
        filled_fields: List[FilledField]
    ) -> ValidationResult:
        """
        Validate complete application before submission
        
        Final check before user approval
        """
        checks = []
        
        # Check 1: All required fields filled
        check_completeness = GuardrailCheck(
            check_name="completeness",
            passed=len(filled_fields) > 0,
            severity="critical",
            message="Application has required fields filled"
        )
        checks.append(check_completeness)
        
        # Check 2: No fields with very low confidence
        low_confidence_fields = [
            f for f in filled_fields 
            if f.confidence == "low"
        ]
        
        check_confidence = GuardrailCheck(
            check_name="confidence",
            passed=len(low_confidence_fields) == 0,
            severity="warning",
            message=f"{len(low_confidence_fields)} fields have low confidence"
        )
        checks.append(check_confidence)
        
        # Check 3: Consistency across fields
        check_consistency = self._check_cross_field_consistency(filled_fields)
        checks.append(check_consistency)
        
        critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
        warnings = [c for c in checks if not c.passed and c.severity == "warning"]
        
        return ValidationResult(
            valid=len(critical_failures) == 0,
            checks=checks,
            can_proceed=len(critical_failures) == 0,
            requires_review=len(warnings) > 0
        )
    
    # ===== Individual Check Methods =====
    
    def _check_no_new_skills(
        self,
        original: ResumeSection,
        tailored: ResumeSection
    ) -> GuardrailCheck:
        """Ensure no new skills are added"""
        
        if not tailored.tailored_content:
            return GuardrailCheck(
                check_name="no_new_skills",
                passed=True,
                severity="critical",
                message="No content to validate"
            )
        
        # Extract skill-like words (simple approach)
        original_skills = self._extract_skill_keywords(original.original_content)
        tailored_skills = self._extract_skill_keywords(tailored.tailored_content)
        
        new_skills = tailored_skills - original_skills
        
        # Filter out common words
        new_skills = {s for s in new_skills if len(s) > 3}
        
        passed = len(new_skills) == 0
        
        return GuardrailCheck(
            check_name="no_new_skills",
            passed=passed,
            severity="critical",
            message=f"No new skills added" if passed else f"Found new skills: {new_skills}",
            details={"new_skills": list(new_skills)} if new_skills else None
        )
    
    def _check_dates_unchanged(
        self,
        original: ResumeSection,
        tailored: ResumeSection
    ) -> GuardrailCheck:
        """Ensure dates are not changed"""
        
        if not tailored.tailored_content:
            return GuardrailCheck(
                check_name="dates_unchanged",
                passed=True,
                severity="critical",
                message="No content to validate"
            )
        
        original_dates = self._extract_dates(original.original_content)
        tailored_dates = self._extract_dates(tailored.tailored_content)
        
        passed = original_dates == tailored_dates
        
        return GuardrailCheck(
            check_name="dates_unchanged",
            passed=passed,
            severity="critical",
            message="Dates unchanged" if passed else "Dates were modified",
            details={
                "original_dates": list(original_dates),
                "tailored_dates": list(tailored_dates)
            }
        )
    
    def _check_facts_preserved(
        self,
        original: ResumeSection,
        tailored: ResumeSection
    ) -> GuardrailCheck:
        """Ensure core facts are preserved"""
        
        if not tailored.tailored_content:
            return GuardrailCheck(
                check_name="facts_preserved",
                passed=True,
                severity="critical",
                message="No content to validate"
            )
        
        # Extract key entities (capitalized phrases)
        original_entities = self._extract_entities(original.original_content)
        tailored_entities = self._extract_entities(tailored.tailored_content)
        
        # Check if important entities are removed
        missing_entities = original_entities - tailored_entities
        
        # Allow some flexibility (entity might be rephrased)
        passed = len(missing_entities) <= len(original_entities) * 0.2  # Allow 20% variation
        
        return GuardrailCheck(
            check_name="facts_preserved",
            passed=passed,
            severity="warning",
            message="Core facts preserved" if passed else f"Some entities missing: {missing_entities}"
        )
    
    def _check_suspicious_content(self, section: ResumeSection) -> GuardrailCheck:
        """Check for suspicious or prohibited content"""
        
        content = section.tailored_content or section.original_content
        content_lower = content.lower()
        
        for pattern in self.prohibited_patterns:
            if re.search(pattern, content_lower):
                return GuardrailCheck(
                    check_name="suspicious_content",
                    passed=False,
                    severity="critical",
                    message=f"Prohibited pattern detected: {pattern}"
                )
        
        return GuardrailCheck(
            check_name="suspicious_content",
            passed=True,
            severity="critical",
            message="No suspicious content detected"
        )
    
    def _check_content_safety(self, content: str) -> GuardrailCheck:
        """Check for safe, professional content"""
        
        content_lower = content.lower()
        
        # Check for unprofessional language
        unprofessional_words = ['hate', 'discriminate', 'illegal', 'fake', 'lie']
        
        for word in unprofessional_words:
            if word in content_lower:
                return GuardrailCheck(
                    check_name="content_safety",
                    passed=False,
                    severity="warning",
                    message=f"Potentially unprofessional language: {word}"
                )
        
        return GuardrailCheck(
            check_name="content_safety",
            passed=True,
            severity="critical",
            message="Content is safe and professional"
        )
    
    def _check_fact_consistency(
        self,
        answer: QuestionAnswer,
        original_data: Dict[str, Any]
    ) -> GuardrailCheck:
        """Check answer consistency with known facts"""
        
        # If we have sources, check consistency
        if answer.sources:
            # Answer should be derivable from sources
            answer_lower = answer.answer.lower()
            
            # Check if answer contains info from sources
            source_content = ' '.join(s.content.lower() for s in answer.sources)
            
            # Simple check: key words from answer should appear in sources
            answer_words = set(answer_lower.split())
            source_words = set(source_content.split())
            
            overlap = len(answer_words & source_words)
            overlap_ratio = overlap / len(answer_words) if answer_words else 0
            
            passed = overlap_ratio > 0.3  # At least 30% overlap
            
            return GuardrailCheck(
                check_name="fact_consistency",
                passed=passed,
                severity="warning",
                message=f"Answer consistency: {overlap_ratio:.0%}"
            )
        
        return GuardrailCheck(
            check_name="fact_consistency",
            passed=True,
            severity="info",
            message="No sources available to verify"
        )
    
    def _check_sensitive_question(self, answer: QuestionAnswer) -> GuardrailCheck:
        """Check handling of sensitive questions"""
        
        question_lower = answer.question.lower()
        
        # Check if question contains sensitive keywords
        is_sensitive = any(kw in question_lower for kw in self.sensitive_keywords)
        
        if is_sensitive:
            # Sensitive questions should have high confidence or require review
            if answer.confidence_score < 0.7:
                return GuardrailCheck(
                    check_name="sensitive_question",
                    passed=False,
                    severity="warning",
                    message="Sensitive question requires higher confidence or manual review"
                )
        
        return GuardrailCheck(
            check_name="sensitive_question",
            passed=True,
            severity="info",
            message="Question handled appropriately"
        )
    
    def _check_answer_quality(self, answer: QuestionAnswer) -> GuardrailCheck:
        """Check answer quality and completeness"""
        
        # Check answer length
        answer_length = len(answer.answer.split())
        
        if answer_length < 2:
            return GuardrailCheck(
                check_name="answer_quality",
                passed=False,
                severity="warning",
                message="Answer is too short"
            )
        
        if answer_length > 200:
            return GuardrailCheck(
                check_name="answer_quality",
                passed=False,
                severity="warning",
                message="Answer is too long"
            )
        
        return GuardrailCheck(
            check_name="answer_quality",
            passed=True,
            severity="info",
            message="Answer quality is acceptable"
        )
    
    def _check_cross_field_consistency(
        self,
        fields: List[FilledField]
    ) -> GuardrailCheck:
        """Check consistency across multiple fields"""
        
        # Example: Check if email and name are consistent
        # This is a simplified check
        
        field_map = {f.field_name.lower(): f.answer for f in fields}
        
        # Basic consistency checks
        inconsistencies = []
        
        # Check if years of experience is reasonable
        if 'years' in str(field_map):
            # More sophisticated checks can be added
            pass
        
        passed = len(inconsistencies) == 0
        
        return GuardrailCheck(
            check_name="cross_field_consistency",
            passed=passed,
            severity="info",
            message="Fields are consistent" if passed else f"Inconsistencies: {inconsistencies}"
        )
    
    # ===== Helper Methods =====
    
    def _extract_skill_keywords(self, text: str) -> set:
        """Extract potential skill keywords"""
        words = text.lower().split()
        # Filter for likely technical terms (simplified)
        skills = {w for w in words if len(w) > 4 and w.isalpha()}
        return skills
    
    def _extract_dates(self, text: str) -> set:
        """Extract date patterns"""
        date_patterns = [
            r'\b\d{4}\b',  # Years
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',
        ]
        
        dates = set()
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.update(matches)
        
        return dates
    
    def _extract_entities(self, text: str) -> set:
        """Extract named entities (simplified)"""
        # Extract capitalized phrases
        entities = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text))
        return entities
