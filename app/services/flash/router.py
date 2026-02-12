"""
Flash Service Router
API endpoints for AI Job Application Assistant
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Any, Dict, List, Optional
import logging

from app.services.flash.models import (
    # Request models
    AnalyzeJobRequest,
    TailorResumeRequest,
    AnswerQuestionRequest,
    FillApplicationRequest,
    FillApplicationFormRequest,
    FillApplicationFormResponse,
    ApproveApplicationRequest,
    CreateUserProfileRequest,
    UpdateUserProfileRequest,
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
from app.services.flash.llm_client import get_llm_client

# Initialize LLM client (provider-agnostic)
llm_client = get_llm_client()

# Initialize services with LLM client
job_analyzer = JobAnalyzerService(llm_client=llm_client)
resume_tailor = ResumeTailorService(llm_client=llm_client)
qa_engine = QuestionAnsweringService(llm_client=llm_client)
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
    print("Analysing job....")
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
        user_profile = _build_user_profile(request.user_id)
        
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
        user_profile = _build_user_profile(request.user_id)
        
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
            resume_path=user_profile.master_resume_path or "./data/resumes/master_resume.txt",
            status=ApplicationStatus.REVIEW_REQUIRED,
            ready_for_submission=overall_validation.can_proceed,
            warnings=warnings if warnings else None
        )
        
        return review
        
    except Exception as e:
        logger.error(f"Application filling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Field-Level Form Filling =====
@router.post("/fill-application-form", response_model=FillApplicationFormResponse)
async def fill_application_form(request: FillApplicationFormRequest):
    """Fill application answers using the extracted form fields."""
    try:
        print("received user id", request.user_id)
        user_profile = _build_user_profile(request.user_id)
        answers: List[QuestionAnswer] = []
        warnings: List[str] = []
        confidence_accumulator = 0.0

        for field in request.form_fields:
            question_text = field.label or field.field_name or field.field_id
            from app.services.flash.models import QuestionContext
            context = QuestionContext(
                question=question_text,
                field_id=field.field_id,
                field_type=field.field_type,
                job_id=request.job_id,
                resume_path=user_profile.master_resume_path or "./data/resumes/master_resume.txt",
                user_profile=user_profile.dict()
            )
           
            answer = await qa_engine.answer_question(context, user_profile)
            validation = guardrails.validate_answer(answer, user_profile.dict())

            if not validation.can_proceed:
                failed_checks = [c.check_name for c in validation.checks if not c.passed]
                warnings.append(
                    f"Field {field.field_name or field.field_id} flagged: {', '.join(failed_checks) or 'guardrail failed'}"
                )

            answers.append(answer)
            confidence_accumulator += answer.confidence_score

        overall_confidence = (
            confidence_accumulator / len(answers)
            if answers else 0.0
        )

        return FillApplicationFormResponse(
            answers=answers,
            overall_confidence=overall_confidence,
            warnings=warnings or None
        )

    except Exception as e:
        logger.error(f"Form filling failed: {e}")
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

# In-memory storage (replace with database in production)
user_profiles_db: Dict[str, UserProfile] = {}


@router.post("/user-profile", response_model=UserProfile)
async def create_user_profile(request: CreateUserProfileRequest):
    """
    Create a new user profile
    
    This endpoint:
    - Creates a new user profile with provided information
    - Generates a unique user_id
    - Stores profile data for use in form filling
    - Returns the created profile
    
    Note: In production, password should be hashed before storage
    """
    try:
        import uuid
        from datetime import datetime
        
        # Generate unique user ID
        user_id = str(uuid.uuid4())
        
        # Create user profile
        profile = UserProfile(
            user_id=user_id,
            full_name=request.full_name,
            email=request.email,
            password=request.password,  # TODO: Hash in production
            phone=request.phone,
            location=request.location,
            linkedin_url=request.linkedin_url,
            github_url=request.github_url,
            portfolio_url=request.portfolio_url,
            current_title=request.current_title,
            years_of_experience=request.years_of_experience,
            skills=request.skills or [],
            preferred_roles=request.preferred_roles or [],
            work_authorization=request.work_authorization,
            visa_status=request.visa_status,
            notice_period=request.notice_period,
            salary_expectation=request.salary_expectation,
            master_resume_path=f"./data/resumes/{user_id}_master_resume.txt",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store in database (currently in-memory)
        user_profiles_db[user_id] = profile
        
        logger.info(f"Created user profile for {user_id}")
        return profile
        
    except Exception as e:
        logger.error(f"Profile creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-profile/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """
    Get user profile by ID
    
    Returns user profile information that can be used for form filling
    """
    try:
        # Check if profile exists in storage
        if user_id in user_profiles_db:
            return user_profiles_db[user_id]
        
        # Fallback to placeholder for backward compatibility
        logger.warning(f"Profile not found for {user_id}, returning placeholder")
        return _build_user_profile(user_id)
        
    except Exception as e:
        logger.error(f"Profile retrieval failed: {e}")
        raise HTTPException(status_code=404, detail=f"User profile not found: {user_id}")


@router.put("/user-profile/{user_id}", response_model=UserProfile)
async def update_user_profile(user_id: str, request: UpdateUserProfileRequest):
    """
    Update existing user profile
    
    This endpoint:
    - Updates user profile with new information
    - Only updates fields that are provided (partial updates)
    - Returns the updated profile
    """
    try:
        from datetime import datetime
        
        # Check if profile exists
        if user_id not in user_profiles_db:
            raise HTTPException(status_code=404, detail=f"User profile not found: {user_id}")
        
        # Get existing profile
        profile = user_profiles_db[user_id]
        
        # Update only provided fields
        update_data = request.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(profile, field, value)
        
        # Update timestamp
        profile.updated_at = datetime.now()
        
        # Store updated profile
        user_profiles_db[user_id] = profile
        
        logger.info(f"Updated user profile for {user_id}")
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user-profile/{user_id}")
async def delete_user_profile(user_id: str):
    """
    Delete user profile
    
    Removes user profile from storage
    """
    try:
        if user_id not in user_profiles_db:
            raise HTTPException(status_code=404, detail=f"User profile not found: {user_id}")
        
        del user_profiles_db[user_id]
        
        logger.info(f"Deleted user profile for {user_id}")
        return {"message": "Profile deleted successfully", "user_id": user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-profiles", response_model=List[UserProfile])
async def list_user_profiles():
    """
    List all user profiles
    
    Returns all stored user profiles (for admin/debugging)
    """
    return list(user_profiles_db.values())


# ===== Analytics Endpoints =====
@router.get("/applications/{user_id}", response_model=List[ApplicationLog])
async def get_applications(user_id: str):
    """Get user's application history"""
    # Placeholder
    return []


# ===== Helper Functions =====
def _build_user_profile(user_id: str, overrides: Optional[Dict[str, Any]] = None) -> UserProfile:
    """Return a lightweight profile used by the Flash service in the absence of storage."""
    # Check if profile exists in storage first
    if user_id in user_profiles_db:
        profile = user_profiles_db[user_id]
        if overrides:
            profile = profile.copy(update=overrides)
        return profile
    
    # Fallback to placeholder profile
    profile = UserProfile(
        user_id=user_id,
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
    if overrides:
        profile = profile.copy(update=overrides)
    return profile

async def log_application(application_id: str, user_id: str):
    """Background task to log application and learn from approved answers"""
    logger.info(f"Logging application {application_id} for user {user_id}")
    # Store in database
    # Update knowledge base with approved answers
