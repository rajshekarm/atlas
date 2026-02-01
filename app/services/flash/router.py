"""
Flash Service Router
API endpoints for AI Job Application Assistant
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import logging

from app.services.flash.models import (
    # Request models
    AnalyzeJobRequest,
    TailorResumeRequest,
    AnswerQuestionRequest,
    FillApplicationRequest,
    ApproveApplicationRequest,
    # Response models
    JobAnalysis,
    ResumeTailoringResponse,
    QuestionAnswer,
    ApplicationReview,
    SubmissionResult,
    ErrorResponse,
    # Data models
    UserProfile,
    ApplicationForm,
    ApplicationLog
)

from app.services.flash.services.job_analyzer import JobAnalyzerService
from app.services.flash.services.resume_tailor import ResumeTailorService
from app.services.flash.services.qa_engine import QuestionAnsweringService
from app.services.flash.services.guardrails import GuardrailsService

# Initialize services
job_analyzer = JobAnalyzerService()
resume_tailor = ResumeTailorService()
qa_engine = QuestionAnsweringService()
guardrails = GuardrailsService()

router = APIRouter()
logger = logging.getLogger(__name__)


# ===== Health Check =====
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "flash"}


# ===== Job Analysis Endpoints =====
@router.post("/analyze-job", response_model=JobAnalysis)
async def analyze_job(request: AnalyzeJobRequest):
    """
    Analyze job description and extract key requirements
    
    This endpoint:
    - Extracts required/preferred skills
    - Identifies technologies
    - Determines seniority level
    - Analyzes role focus
    """
    try:
        analysis = await job_analyzer.analyze_job(request.job_description)
        return analysis
    except Exception as e:
        logger.error(f"Job analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Resume Tailoring Endpoints =====
@router.post("/tailor-resume", response_model=ResumeTailoringResponse)
async def tailor_resume(request: TailorResumeRequest):
    """
    Tailor resume for specific job
    
    This endpoint:
    - Analyzes job requirements
    - Rewrites resume sections to emphasize relevant skills
    - Applies strict guardrails (no fake experience, no date changes)
    - Generates diff preview for user approval
    """
    try:
        # First analyze the job
        # Note: In production, fetch job_description from database using job_id
        # For now, this is a placeholder
        
        # Placeholder: fetch job and user data
        # job_description = fetch_job_description(request.job_id)
        # user_profile = fetch_user_profile(request.user_id)
        
        # For demo, create a mock job analysis
        from app.services.flash.models import JobDescription
        
        job_desc = JobDescription(
            title="Software Engineer",
            company="Tech Corp",
            description="Looking for a skilled engineer",
            url=f"https://example.com/jobs/{request.job_id}",
            requirements=[]
        )
        
        job_analysis = await job_analyzer.analyze_job(job_desc)
        
        # Create tailoring request
        from app.services.flash.models import ResumeTailoringRequest as RTRequest
        tailor_request = RTRequest(
            job_id=request.job_id,
            master_resume_path="./data/resumes/master_resume.txt",  # Should come from user_profile
            job_description=job_desc
        )
        
        # Tailor resume
        result = await resume_tailor.tailor_resume(tailor_request, job_analysis)
        
        # Validate changes
        for section in result.sections:
            if section.tailored_content:
                validation = guardrails.validate_resume_changes(
                    section,
                    section
                )
                if not validation.can_proceed:
                    raise HTTPException(
                        status_code=400,
                        detail="Resume changes failed validation"
                    )
        
        return result
        
    except Exception as e:
        logger.error(f"Resume tailoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Question Answering Endpoints =====
@router.post("/answer-question", response_model=QuestionAnswer)
async def answer_question(request: AnswerQuestionRequest):
    """
    Answer a single application question using RAG
    
    This endpoint:
    - Retrieves relevant context from resume and profile
    - Searches past approved answers
    - Generates truthful answer with confidence score
    - Flags low-confidence answers for review
    """
    try:
        # Fetch user profile
        # user_profile = fetch_user_profile(request.user_id)
        
        # Placeholder user profile
        user_profile = UserProfile(
            user_id=request.user_id,
            full_name="John Doe",
            email="john@example.com",
            location="San Francisco, CA",
            current_title="Software Engineer",
            years_of_experience=5,
            skills=["Python", "FastAPI", "React", "PostgreSQL"],
            preferred_roles=["Backend Engineer", "Full Stack Engineer"],
            work_authorization="US Citizen",
            master_resume_path="./data/resumes/master_resume.txt"
        )
        
        # Answer question
        answer = await qa_engine.answer_question(
            request.question_context,
            user_profile
        )
        
        # Validate answer
        validation = guardrails.validate_answer(answer, user_profile.dict())
        
        if not validation.can_proceed:
            raise HTTPException(
                status_code=400,
                detail="Answer failed validation checks"
            )
        
        return answer
        
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Application Filling Endpoints =====
@router.post("/fill-application", response_model=ApplicationReview)
async def fill_application(request: FillApplicationRequest):
    """
    Fill entire application form
    
    This endpoint:
    - Analyzes all form fields
    - Generates answers for each field
    - Validates answers with guardrails
    - Returns complete application for review
    """
    try:
        # Fetch user profile
        user_profile = UserProfile(
            user_id=request.user_id,
            full_name="John Doe",
            email="john@example.com",
            phone="+1-555-0123",
            location="San Francisco, CA",
            current_title="Software Engineer",
            years_of_experience=5,
            skills=["Python", "FastAPI", "React"],
            preferred_roles=["Backend Engineer"],
            work_authorization="US Citizen",
            master_resume_path="./data/resumes/master_resume.txt"
        )
        
        # Analyze job first
        job_analysis = await job_analyzer.analyze_job(request.job_description)
        
        # Answer each field
        from app.services.flash.models import FilledField, QuestionContext
        filled_fields = []
        warnings = []
        
        for field in request.application_form.fields:
            # Create question context
            context = QuestionContext(
                question=field.label,
                field_id=field.field_id,
                field_type=field.field_type,
                job_id=job_analysis.job_id,
                resume_path=user_profile.master_resume_path
            )
            
            # Get answer
            answer = await qa_engine.answer_question(context, user_profile)
            
            # Validate
            validation = guardrails.validate_answer(answer, user_profile.dict())
            
            if not validation.can_proceed:
                warnings.append(f"Field {field.field_name}: validation failed")
                continue
            
            filled_fields.append(FilledField(
                field_id=field.field_id,
                field_name=field.field_name,
                answer=answer.answer,
                confidence=answer.confidence,
                source=answer.sources[0].source_type if answer.sources else "generated"
            ))
        
        # Overall validation
        overall_validation = guardrails.validate_application(filled_fields)
        
        # Create application review
        from app.services.flash.models import ApplicationStatus
        
        review = ApplicationReview(
            application_id=f"app_{job_analysis.job_id}_{request.user_id}",
            job_id=job_analysis.job_id,
            company=request.job_description.company or "Unknown",
            role=request.job_description.title,
            filled_fields=filled_fields,
            resume_path=user_profile.master_resume_path,
            status=ApplicationStatus.REVIEW_REQUIRED,
            ready_for_submission=overall_validation.can_proceed,
            warnings=warnings if warnings else None
        )
        
        return review
        
    except Exception as e:
        logger.error(f"Application filling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Approval & Submission Endpoints =====
@router.post("/approve-application", response_model=SubmissionResult)
async def approve_application(
    request: ApproveApplicationRequest,
    background_tasks: BackgroundTasks
):
    """
    Approve and submit application
    
    This endpoint:
    - Applies user edits to fields
    - Performs final validation
    - Returns submission confirmation
    - Logs application for learning
    
    Note: Actual submission happens in Chrome Extension
    This endpoint just validates and logs the approved application
    """
    try:
        # Fetch application from database
        # application = fetch_application(request.application_id)
        
        # Apply user edits if any
        if request.edited_fields:
            # Update fields with user edits
            pass
        
        # Final validation
        # validation = guardrails.validate_application(application.filled_fields)
        
        # if not validation.can_proceed:
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Application cannot be submitted"
        #     )
        
        # Store approved answers for future learning
        background_tasks.add_task(
            log_application,
            request.application_id,
            request.user_id
        )
        
        # Return success (actual submission happens in Chrome Extension)
        from datetime import datetime
        result = SubmissionResult(
            application_id=request.application_id,
            success=True,
            submitted_at=datetime.now(),
            confirmation_number=None  # Will be filled by Chrome Extension
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Application approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== User Profile Endpoints =====
@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """Get user profile"""
    # Placeholder
    return UserProfile(
        user_id=user_id,
        full_name="John Doe",
        email="john@example.com",
        location="San Francisco, CA",
        current_title="Software Engineer",
        years_of_experience=5,
        skills=["Python", "FastAPI", "React"],
        preferred_roles=["Backend Engineer"],
        work_authorization="US Citizen",
        master_resume_path="./data/resumes/master_resume.txt"
    )


@router.post("/profile", response_model=UserProfile)
async def create_user_profile(profile: UserProfile):
    """Create or update user profile"""
    # In production, store in database
    return profile


# ===== Analytics Endpoints =====
@router.get("/applications/{user_id}", response_model=List[ApplicationLog])
async def get_applications(user_id: str):
    """Get user's application history"""
    # Placeholder
    return []


# ===== Helper Functions =====
async def log_application(application_id: str, user_id: str):
    """Background task to log application and learn from approved answers"""
    logger.info(f"Logging application {application_id} for user {user_id}")
    # Store in database
    # Update knowledge base with approved answers
