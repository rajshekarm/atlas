"""
Flash Service Router
API endpoints for AI Job Application Assistant
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from typing import Any, Dict, List, Optional
import logging

from app.core.auth import get_current_user_id, get_optional_user_id
from app.services.auth.models import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    AuthResponse,
    AuthData,
    UserResponse,
    RefreshTokenResponse,
    RefreshToken
)
from app.services.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)
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
    AnswerSource,
    ConfidenceLevel,
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


# ===== Authentication Storage =====
# In-memory storage (replace with database in production)
auth_users_db: Dict[str, dict] = {}  # email -> user data
auth_refresh_tokens_db: Dict[str, RefreshToken] = {}  # token -> RefreshToken


# ===== Health Check =====
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "flash"}


# ========================================
# 🔐 AUTHENTICATION ENDPOINTS
# ========================================

@router.post("/auth/register", response_model=AuthResponse, tags=["Authentication"])
async def register(request: RegisterRequest):
    """
    Register a new user
    
    This endpoint:
    - Validates email is not already registered
    - Hashes the password
    - Creates user account
    - Generates access and refresh tokens
    - Returns user data and tokens
    """
    try:
        # Check if user already exists
        if request.email in auth_users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Generate user ID
        import uuid
        user_id = f"user_{uuid.uuid4().hex[:10]}"
        
        # Create user
        from datetime import datetime
        user_data = {
            "id": user_id,
            "name": request.name,
            "email": request.email,
            "password": hashed_password,
            # Dev-only convenience for auto-fill flows that require credential replay.
            # Replace with encrypted credential vault before production.
            "latest_login_password": request.password,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store user
        auth_users_db[request.email] = user_data
        
        # Generate tokens
        access_token, access_expires = create_access_token(user_id, request.email)
        refresh_token, refresh_expires = create_refresh_token(user_id)
        
        # Store refresh token
        auth_refresh_tokens_db[refresh_token] = RefreshToken(
            token=refresh_token,
            user_id=user_id,
            expires_at=refresh_expires
        )
        
        # Create response
        user_response = UserResponse(
            id=user_id,
            name=request.name,
            email=request.email
        )
        
        auth_data = AuthData(
            user=user_response,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=access_expires.isoformat() + "Z"
        )
        
        logger.info(f"User registered: {request.email}")
        
        return AuthResponse(success=True, data=auth_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/auth/login", response_model=AuthResponse, tags=["Authentication"])
async def login(request: LoginRequest):
    """
    Login an existing user
    
    This endpoint:
    - Validates email and password
    - Generates new access and refresh tokens
    - Returns user data and tokens
    """
    try:
        # Check if user exists
        if request.email not in auth_users_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_data = auth_users_db[request.email]
        
        # Verify password
        if not verify_password(request.password, user_data["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Keep latest successful plaintext credential in memory for auth-form replay.
        # Replace with encrypted credential vault before production.
        user_data["latest_login_password"] = request.password
        
        # Generate tokens
        access_token, access_expires = create_access_token(
            user_data["id"], 
            request.email
        )
        refresh_token, refresh_expires = create_refresh_token(user_data["id"])
        
        # Store refresh token
        auth_refresh_tokens_db[refresh_token] = RefreshToken(
            token=refresh_token,
            user_id=user_data["id"],
            expires_at=refresh_expires
        )
        
        # Create response
        user_response = UserResponse(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"]
        )
        
        auth_data = AuthData(
            user=user_response,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=access_expires.isoformat() + "Z"
        )
        
        logger.info(f"User logged in: {request.email}")
        
        return AuthResponse(success=True, data=auth_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/auth/refresh", response_model=RefreshTokenResponse, tags=["Authentication"])
async def refresh(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    This endpoint:
    - Validates refresh token
    - Generates new access token
    - Returns new access token and expiration
    """
    try:
        from datetime import datetime
        
        # Check if refresh token exists
        if request.refresh_token not in auth_refresh_tokens_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        refresh_token_data = auth_refresh_tokens_db[request.refresh_token]
        
        # Check if refresh token is expired
        if datetime.utcnow() > refresh_token_data.expires_at:
            # Clean up expired token
            del auth_refresh_tokens_db[request.refresh_token]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        
        # Get user data
        user_id = refresh_token_data.user_id
        user_email = None
        
        # Find user email
        for email, user_data in auth_users_db.items():
            if user_data["id"] == user_id:
                user_email = email
                break
        
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Generate new access token
        access_token, access_expires = create_access_token(user_id, user_email)
        
        logger.info(f"Token refreshed for user: {user_id}")
        
        return RefreshTokenResponse(
            access_token=access_token,
            expires_at=access_expires.isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/auth/logout", tags=["Authentication"])
async def logout(request: RefreshTokenRequest):
    """
    Logout user by invalidating refresh token
    
    This endpoint:
    - Invalidates the provided refresh token
    - Returns success message
    """
    try:
        # Remove refresh token if it exists
        if request.refresh_token in auth_refresh_tokens_db:
            del auth_refresh_tokens_db[request.refresh_token]
            logger.info(f"User logged out")
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(user_id: str = Depends(get_current_user_id)):
    """
    Get current user information from access token
    
    Requires: Authorization header with valid JWT token
    Returns: User information
    """
    try:
        # Find user in database
        for email, user_data in auth_users_db.items():
            if user_data["id"] == user_id:
                return UserResponse(
                    id=user_data["id"],
                    name=user_data["name"],
                    email=user_data["email"]
                )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# 🎯 FLASH SERVICE ENDPOINTS
# ========================================


# ===== Protected Example Endpoint =====
@router.get("/protected-test")
async def protected_test(user_id: str = Depends(get_current_user_id)):
    """
    Example protected endpoint - requires valid JWT token
    
    This demonstrates how Flash service can verify authentication.
    Send request with header: Authorization: Bearer <access_token>
    """
    return {
        "message": "Authentication verified!",
        "authenticated_user_id": user_id,
        "service": "flash"
    }


# ===== Job Analysis Endpoints =====
@router.post("/analyze-job", response_model=JobAnalysis)
async def analyze_job(
    request: AnalyzeJobRequest,
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Analyze job description and extract key requirements
    
    This endpoint:
    - Extracts required/preferred skills
    - Identifies technologies
    - Determines seniority level
    - Analyzes role focus
    
    Authentication: Optional (works without token, but can track if provided)
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
        logger.info(
            "[fill-application-form] request received user_id=%s job_id=%s field_count=%d",
            request.user_id,
            request.job_id or "unknown_job",
            len(request.form_fields),
        )
        profile_overrides = dict(request.user_profile or {})
        # Normalize common frontend keys before applying overrides.
        if "full_name" not in profile_overrides and "name" in profile_overrides:
            profile_overrides["full_name"] = profile_overrides["name"]
        if "phone" not in profile_overrides and "phoneNumber" in profile_overrides:
            profile_overrides["phone"] = profile_overrides["phoneNumber"]
        if "address_line_1" not in profile_overrides and "addressLine1" in profile_overrides:
            profile_overrides["address_line_1"] = profile_overrides["addressLine1"]
        if "address_line_2" not in profile_overrides and "addressLine2" in profile_overrides:
            profile_overrides["address_line_2"] = profile_overrides["addressLine2"]
        if "state" not in profile_overrides and "countryRegion" in profile_overrides:
            profile_overrides["state"] = profile_overrides["countryRegion"]
        if "postal_code" not in profile_overrides and "postalCode" in profile_overrides:
            profile_overrides["postal_code"] = profile_overrides["postalCode"]
        if "country_phone_code" not in profile_overrides and "phoneNumber--countryPhoneCode" in profile_overrides:
            profile_overrides["country_phone_code"] = profile_overrides["phoneNumber--countryPhoneCode"]
        if "phone_extension" not in profile_overrides and "phoneNumber--extension" in profile_overrides:
            profile_overrides["phone_extension"] = profile_overrides["phoneNumber--extension"]
        if "password" not in profile_overrides and "passoword" in profile_overrides:
            profile_overrides["password"] = profile_overrides["passoword"]
        profile_overrides.pop("id", None)
        user_profile = _build_user_profile(
            request.user_id,
            overrides=profile_overrides or None
        )
        auth_password = _get_auth_password(request.user_id) or ""
        answers: List[QuestionAnswer] = []
        warnings: List[str] = []
        confidence_accumulator = 0.0

        def _norm(*values: Optional[str]) -> str:
            return " ".join([(v or "").strip().lower() for v in values]).strip()

        auth_keywords = (
            "sign in",
            "signin",
            "login",
            "log in",
            "sign up",
            "signup",
            "register",
            "create account",
            "account",
        )

        page_text = " ".join(
            _norm(field.label, field.field_name, field.placeholder)
            for field in request.form_fields
        )
        has_password_field = any(
            "password" in _norm(field.label, field.field_name, field.placeholder)
            for field in request.form_fields
        )
        is_auth_page = has_password_field and any(keyword in page_text for keyword in auth_keywords)
        logger.info(
            "[fill-application-form] page classified is_auth_page=%s has_password_field=%s",
            is_auth_page,
            has_password_field,
        )
        url_pool: List[str] = [
            url.strip()
            for url in [
                user_profile.linkedin_url,
                user_profile.github_url,
                user_profile.portfolio_url,
                user_profile.website_url,
                user_profile.twitter_url,
                user_profile.workday_profile_url,
            ]
            if isinstance(url, str) and url.strip()
        ]
        used_urls: set[str] = set()

        def _consume_next_url(preferred: Optional[str] = None) -> str:
            if preferred and preferred.strip():
                preferred_value = preferred.strip()
                if preferred_value not in used_urls:
                    used_urls.add(preferred_value)
                    return preferred_value
            for candidate in url_pool:
                if candidate not in used_urls:
                    used_urls.add(candidate)
                    return candidate
            return preferred.strip() if isinstance(preferred, str) and preferred.strip() else ""

        # Workday often emits duplicate logical questions (hidden text + visible dropdown).
        # Keep a single best candidate per logical question to avoid conflicting answers.
        field_priority = {
            "dropdown": 4,
            "radio": 4,
            "checkbox": 3,
            "textarea": 2,
            "text": 1,
            "email": 1,
            "phone": 1,
            "date": 1,
            "file": 1,
        }
        deduped_by_key: Dict[str, Any] = {}
        for raw_field in request.form_fields:
            dedupe_key = _norm(raw_field.label, raw_field.placeholder, raw_field.field_name)
            if not dedupe_key:
                dedupe_key = _norm(raw_field.field_id)
            current = deduped_by_key.get(dedupe_key)
            if current is None:
                deduped_by_key[dedupe_key] = raw_field
                continue

            current_score = field_priority.get(str(current.field_type), 0) + (2 if current.options else 0) + (1 if current.required else 0)
            new_score = field_priority.get(str(raw_field.field_type), 0) + (2 if raw_field.options else 0) + (1 if raw_field.required else 0)
            if new_score >= current_score:
                deduped_by_key[dedupe_key] = raw_field

        selected_fields = list(deduped_by_key.values())
        logger.info(
            "[fill-application-form] deduped fields original=%d selected=%d",
            len(request.form_fields),
            len(selected_fields),
        )

        for index, field in enumerate(selected_fields, start=1):
            logger.info(
                "[fill-application-form] processing field %d/%d field_id=%s field_name=%s type=%s required=%s",
                index,
                len(selected_fields),
                field.field_id,
                field.field_name,
                field.field_type,
                field.required,
            )
            field_text = _norm(field.label, field.field_name, field.placeholder)
            field_key = _norm(field.field_id, field.field_name, field.label)

            # Always handle password fields deterministically from profile.
            # This prevents password fields from reaching QA and returning "Not provided".
            if "password" in field_text:
                password_answer = auth_password or user_profile.password or ""
                if not password_answer and field.required:
                    warnings.append(f"Missing value for auth field: {field.field_name or field.field_id}")

                direct_password_answer = QuestionAnswer(
                    field_id=field.field_id,
                    question=field.label or field.field_name or field.field_id,
                    answer=password_answer,
                    confidence=ConfidenceLevel.HIGH if password_answer else ConfidenceLevel.LOW,
                    confidence_score=1.0 if password_answer else 0.2,
                    sources=[
                        AnswerSource(
                            source_type="profile",
                            content="user_profile",
                            relevance_score=1.0 if password_answer else 0.2
                        )
                    ],
                    requires_review=False if password_answer else True
                )
                answers.append(direct_password_answer)
                confidence_accumulator += direct_password_answer.confidence_score
                logger.info(
                    "[fill-application-form] password answer prepared field_id=%s answer_len=%d",
                    field.field_id,
                    len(password_answer),
                )
                continue

            # Deterministic profile mapping for common personal/contact fields.
            # This avoids sending obvious profile-backed fields to QA, which can
            # otherwise return "Not provided" for structured data.
            direct_profile_answer: Optional[str] = None
            if "email" in field_text:
                direct_profile_answer = user_profile.email or ""
            elif "first name" in field_text or "firstname" in field_key:
                direct_profile_answer = (
                    user_profile.first_name
                    or ((user_profile.full_name or "").split(" ")[0] if user_profile.full_name else "")
                )
            elif "last name" in field_text or "lastname" in field_key:
                direct_profile_answer = (
                    user_profile.last_name
                    or (
                        user_profile.full_name.split(" ", 1)[1]
                        if user_profile.full_name and " " in user_profile.full_name
                        else ""
                    )
                )
            elif "full name" in field_text or field_text == "name":
                direct_profile_answer = user_profile.full_name or ""
            elif "address line 1" in field_text or "addressline1" in field_key:
                direct_profile_answer = user_profile.address_line_1 or ""
            elif "address line 2" in field_text or "addressline2" in field_key:
                direct_profile_answer = user_profile.address_line_2 or ""
            elif "city" in field_text:
                direct_profile_answer = user_profile.city or ""
            elif (
                "state" in field_text
                or "province" in field_text
                or "countryregion" in field_key
                or "region" in field_key
            ):
                direct_profile_answer = user_profile.state or ""
            elif "postal code" in field_text or "zip" in field_text or "postalcode" in field_key:
                direct_profile_answer = user_profile.postal_code or ""
            elif "county" in field_text:
                direct_profile_answer = user_profile.county or ""
            elif "country" in field_text:
                direct_profile_answer = user_profile.country or ""
            elif "phone extension" in field_text or "extension" in field_key:
                direct_profile_answer = user_profile.phone_extension or ""
            elif "phone device type" in field_text or "phonetype" in field_key:
                direct_profile_answer = user_profile.phone_type or ""
            elif "country phone code" in field_text or "countryphonecode" in field_key:
                direct_profile_answer = user_profile.country_phone_code or ""
            elif "phone" in field_text:
                direct_profile_answer = user_profile.phone or ""
            elif "sponsorship" in field_text or "visa" in field_text:
                if user_profile.requires_visa_sponsorship is not None:
                    direct_profile_answer = "Yes" if user_profile.requires_visa_sponsorship else "No"
                elif user_profile.visa_status:
                    direct_profile_answer = user_profile.visa_status
            elif (
                "legally authorized" in field_text
                or "authorized to work" in field_text
                or ("authorization" in field_text and "work" in field_text)
            ):
                if user_profile.legally_authorized_to_work is not None:
                    direct_profile_answer = "Yes" if user_profile.legally_authorized_to_work else "No"
                elif user_profile.work_authorization:
                    direct_profile_answer = user_profile.work_authorization
            elif (
                "github" in field_text
                or "github" in field_key
                or "linkedin" in field_text
                or "linkedin" in field_key
                or "portfolio" in field_text
                or "portfolio" in field_key
                or "website" in field_text
                or "website" in field_key
                or "url" in field_text
                or "link" in field_text
                or "webaddress" in field_key
            ):
                if "github" in field_text or "github" in field_key:
                    direct_profile_answer = _consume_next_url(user_profile.github_url)
                elif "linkedin" in field_text or "linkedin" in field_key:
                    direct_profile_answer = _consume_next_url(user_profile.linkedin_url)
                elif "portfolio" in field_text or "portfolio" in field_key:
                    direct_profile_answer = _consume_next_url(user_profile.portfolio_url)
                elif "twitter" in field_text or "twitter" in field_key:
                    direct_profile_answer = _consume_next_url(user_profile.twitter_url)
                elif "workday" in field_text or "workday" in field_key:
                    direct_profile_answer = _consume_next_url(user_profile.workday_profile_url)
                else:
                    direct_profile_answer = _consume_next_url(user_profile.website_url)

            if direct_profile_answer is not None:
                if not direct_profile_answer and field.required:
                    warnings.append(f"Missing value for profile field: {field.field_name or field.field_id}")

                direct_answer = QuestionAnswer(
                    field_id=field.field_id,
                    question=field.label or field.field_name or field.field_id,
                    answer=direct_profile_answer,
                    confidence=ConfidenceLevel.HIGH if direct_profile_answer else ConfidenceLevel.LOW,
                    confidence_score=1.0 if direct_profile_answer else 0.2,
                    sources=[
                        AnswerSource(
                            source_type="profile",
                            content="user_profile",
                            relevance_score=1.0 if direct_profile_answer else 0.2
                        )
                    ],
                    requires_review=False if direct_profile_answer else True
                )
                answers.append(direct_answer)
                confidence_accumulator += direct_answer.confidence_score
                logger.info(
                    "[fill-application-form] direct profile answer field_id=%s answer_len=%d",
                    field.field_id,
                    len(direct_answer.answer or ""),
                )
                continue

            if is_auth_page:
                answer_text = ""

                if "password" in field_text:
                    answer_text = user_profile.password or ""
                elif "email" in field_text or "username" in field_text:
                    answer_text = user_profile.email or ""
                elif "full name" in field_text or field_text == "name":
                    answer_text = user_profile.full_name or ""
                elif "first name" in field_text:
                    answer_text = (user_profile.full_name or "").split(" ")[0] if user_profile.full_name else ""
                elif "last name" in field_text:
                    if user_profile.full_name and " " in user_profile.full_name:
                        answer_text = user_profile.full_name.split(" ", 1)[1]
                elif "phone" in field_text:
                    answer_text = user_profile.phone or ""

                if not answer_text and field.required:
                    warnings.append(f"Missing value for auth field: {field.field_name or field.field_id}")

                direct_answer = QuestionAnswer(
                    field_id=field.field_id,
                    question=field.label or field.field_name or field.field_id,
                    answer=answer_text,
                    confidence=ConfidenceLevel.HIGH if answer_text else ConfidenceLevel.LOW,
                    confidence_score=1.0 if answer_text else 0.2,
                    sources=[
                        AnswerSource(
                            source_type="profile",
                            content="user_profile",
                            relevance_score=1.0 if answer_text else 0.2
                        )
                    ],
                    requires_review=False if answer_text else True
                )
                answers.append(direct_answer)
                confidence_accumulator += direct_answer.confidence_score
                logger.info(
                    "[fill-application-form] auth answer prepared field_id=%s answer_len=%d confidence=%.2f",
                    field.field_id,
                    len(direct_answer.answer or ""),
                    direct_answer.confidence_score,
                )
                continue

            question_text = field.label or field.field_name or field.field_id
            from app.services.flash.models import QuestionContext
            context = QuestionContext(
                question=question_text,
                field_id=field.field_id,
                field_type=field.field_type,
                job_id=request.job_id or "unknown_job",
                resume_path=user_profile.master_resume_path or "./data/resumes/master_resume.txt",
                user_profile=user_profile.dict()
            )
            logger.info(
                "[fill-application-form] sending field to QA field_id=%s question=%s",
                field.field_id,
                question_text,
            )
            answer = await qa_engine.answer_question(context, user_profile)
            answers.append(answer)
            confidence_accumulator += answer.confidence_score
            logger.info(
                "[fill-application-form] QA answer ready field_id=%s confidence=%.2f requires_review=%s",
                answer.field_id,
                answer.confidence_score,
                answer.requires_review,
            )

        overall_confidence = (
            confidence_accumulator / len(answers)
            if answers else 0.0
        )
        logger.info(
            "[fill-application-form] response prepared answers=%d overall_confidence=%.2f warnings=%d",
            len(answers),
            overall_confidence,
            len(warnings),
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
async def create_user_profile(
    request: CreateUserProfileRequest,
    authenticated_user_id: str = Depends(get_current_user_id)
):
    """
    Create a new user profile (Protected - requires authentication)
    
    This endpoint:
    - Creates a new user profile for the authenticated user
    - Uses authenticated user_id from JWT token
    - Stores profile data for use in form filling
    - Returns the created profile
    
    Requires: Authorization header with valid JWT token
    """
    try:
        from datetime import datetime
        
        # Use authenticated user ID from token
        user_id = authenticated_user_id
        
        # Create user profile using field names (not alias)
        profile = UserProfile(
            user_id=user_id,
            name=request.full_name,  # Use alias 'name' for construction
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
            education=request.education or [],
            experience=request.experience or [],
            preferred_roles=request.preferred_roles or [],
            work_authorization=request.work_authorization,
            visa_status=request.visa_status,
            notice_period=request.notice_period,
            salary_expectation=request.salary_expectation,
            master_resume_path=f"./data/resumes/{user_id}_master_resume.txt",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Apply all explicitly provided optional fields so profile expansion
        # does not require manual mapping changes in this endpoint.
        create_data = request.model_dump(exclude_unset=True, by_alias=False)
        for field, value in create_data.items():
            if field == "full_name":
                profile.full_name = value
            elif hasattr(profile, field):
                setattr(profile, field, value)
        
        # Store in database (currently in-memory)
        user_profiles_db[user_id] = profile
        
        logger.info(f"Created user profile for {user_id}")
        return profile
        
    except Exception as e:
        logger.error(f"Profile creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-profile/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: str,
    authenticated_user_id: str = Depends(get_current_user_id)
):
    """
    Get user profile by ID (Protected - requires authentication)
    
    Users can only view their own profile
    Returns user profile information that can be used for form filling
    
    Requires: Authorization header with valid JWT token
    """
    try:
        # Verify user is accessing their own profile
        if user_id != authenticated_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own profile"
            )
        
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
async def update_user_profile(
    user_id: str,
    request: UpdateUserProfileRequest,
    authenticated_user_id: str = Depends(get_current_user_id)
):
    """
    Update existing user profile (Protected - requires authentication)
    
    This endpoint:
    - Updates user profile with new information
    - Only updates fields that are provided (partial updates)
    - Users can only update their own profile
    - Returns the updated profile
    
    Requires: Authorization header with valid JWT token
    """
    try:
        from datetime import datetime
        
        # Verify user is updating their own profile
        if user_id != authenticated_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile"
            )
        
        # Upsert behavior: if profile is missing (common with in-memory storage),
        # start from fallback profile and persist it after applying updates.
        profile = user_profiles_db.get(user_id) or _build_user_profile(user_id)
        
        # Update only provided fields (use model_dump for Pydantic v2)
        update_data = request.model_dump(exclude_unset=True, by_alias=False)
        
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
async def delete_user_profile(
    user_id: str,
    authenticated_user_id: str = Depends(get_current_user_id)
):
    """
    Delete user profile (Protected - requires authentication)
    
    Users can only delete their own profile
    Removes user profile from storage
    
    Requires: Authorization header with valid JWT token
    """
    try:
        # Verify user is deleting their own profile
        if user_id != authenticated_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own profile"
            )
        
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
        print(f"user profile for userid : {user_id}")
        profile = user_profiles_db[user_id]
        if overrides:
            profile = profile.copy(update=overrides)
        return profile
    
    # Fallback to placeholder profile
    profile = UserProfile(
        user_id=user_id,
        name="John Doe",  # Use alias 'name'
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


def _get_auth_password(user_id: str) -> Optional[str]:
    """Get latest known plaintext password for a user from in-memory auth store."""
    for user_data in auth_users_db.values():
        if user_data.get("id") == user_id:
            return user_data.get("latest_login_password")
    return None
