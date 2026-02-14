"""
Pydantic models for Flash AI Job Application Assistant
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from enum import Enum


# ===== Enums =====
class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    DROPDOWN = "dropdown"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE = "file"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    FAILED = "failed"


# ===== Job Analysis Models =====
class JobDescription(BaseModel):
    """Job description extracted from the webpage"""
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: str
    requirements: List[str] = []
    responsibilities: List[str] = []
    preferred_qualifications: List[str] = []
    url: str


class JobAnalysis(BaseModel):
    """Analysis result from job description"""
    job_id: str
    required_skills: List[str]
    preferred_skills: List[str]
    technologies: List[str]
    seniority_level: str
    role_focus: str  # backend, frontend, full-stack, devops, etc.
    key_requirements: List[str]
    match_score: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ===== Form Field Models =====
class FormField(BaseModel):
    """Single form field extracted from application page"""
    field_id: str
    field_name: str
    field_type: FieldType
    label: str
    placeholder: Optional[str] = None
    required: bool = False
    options: Optional[List[str]] = None  # for dropdown/radio
    validation_rules: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_client_keys(cls, data: Any) -> Any:
        """Accept browser payload keys: id/type/name."""
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        if "field_id" not in normalized and "id" in normalized:
            normalized["field_id"] = normalized["id"]
        if "field_type" not in normalized and "type" in normalized:
            normalized["field_type"] = normalized["type"]
        if normalized.get("field_type") == "select":
            # Browser extractor uses "select"; backend enum expects "dropdown".
            normalized["field_type"] = "dropdown"
        if normalized.get("field_type") == "password":
            # Backend schema does not include a dedicated password enum.
            # Treat password inputs as text for validation/answer generation.
            normalized["field_type"] = "text"
        if "field_name" not in normalized:
            normalized["field_name"] = (
                normalized.get("name")
                or normalized.get("field_id")
                or normalized.get("id")
                or "unknown_field"
            )

        return normalized


class ApplicationForm(BaseModel):
    """Complete application form structure"""
    form_id: str
    url: str
    job_id: str
    fields: List[FormField]
    steps: Optional[List[str]] = None  # for multi-step forms
    current_step: int = 0


# ===== Resume Models =====
class ResumeSection(BaseModel):
    """Individual section of a resume"""
    section_type: str  # summary, experience, education, skills, etc.
    original_content: str
    tailored_content: Optional[str] = None
    changes: Optional[List[str]] = None


class ResumeTailoringRequest(BaseModel):
    """Request to tailor resume for specific job"""
    job_id: str
    master_resume_path: str
    job_description: JobDescription
    focus_areas: Optional[List[str]] = None


class ResumeTailoringResponse(BaseModel):
    """Tailored resume with diff preview"""
    job_id: str
    original_resume_path: str
    tailored_resume_path: str
    sections: List[ResumeSection]
    changes_summary: str
    confidence: ConfidenceLevel
    requires_approval: bool = True
    timestamp: datetime = Field(default_factory=datetime.now)


# ===== Question Answering Models =====
class QuestionContext(BaseModel):
    """Context for answering a question"""
    question: str
    field_id: str
    field_type: FieldType
    job_id: str
    resume_path: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None


class AnswerSource(BaseModel):
    """Source of information for an answer"""
    source_type: str  # resume, profile, past_answer, inference
    content: str
    relevance_score: float


class QuestionAnswer(BaseModel):
    """AI-generated answer for an application question"""
    field_id: str
    question: str
    answer: str
    confidence: ConfidenceLevel
    confidence_score: float
    sources: List[AnswerSource]
    requires_review: bool
    alternative_answers: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ===== Application Orchestration Models =====
class FilledField(BaseModel):
    """Single filled field with answer"""
    field_id: str
    field_name: str
    answer: str
    confidence: ConfidenceLevel
    source: str


class ApplicationReview(BaseModel):
    """Complete application for review before submission"""
    application_id: str
    job_id: str
    company: str
    role: str
    filled_fields: List[FilledField]
    resume_path: str
    status: ApplicationStatus
    ready_for_submission: bool
    warnings: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SubmissionResult(BaseModel):
    """Result after application submission"""
    application_id: str
    success: bool
    submitted_at: Optional[datetime] = None
    error_message: Optional[str] = None
    confirmation_number: Optional[str] = None


# ===== Guardrails & Validation Models =====
class GuardrailCheck(BaseModel):
    """Result of a guardrail validation"""
    check_name: str
    passed: bool
    severity: str  # critical, warning, info
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Overall validation result"""
    valid: bool
    checks: List[GuardrailCheck]
    can_proceed: bool
    requires_review: bool


# ===== User Profile Models =====
def _normalize_profile_payload_keys(data: Any) -> Any:
    """Normalize common browser/extension profile keys to API model keys."""
    if not isinstance(data, dict):
        return data

    normalized = dict(data)

    key_mapping = {
        "source--source": "referral_source",
        "country--country": "country",
        "legalName--firstName": "first_name",
        "legalName--lastName": "last_name",
        "name--legalName--firstName": "first_name",
        "name--legalName--lastName": "last_name",
        "name--preferredCheck": "preferred_name_opt_in",
        "preferredCheck": "preferred_name_opt_in",
        "address--addressLine1": "address_line_1",
        "address--addressLine2": "address_line_2",
        "addressLine1": "address_line_1",
        "addressLine2": "address_line_2",
        "address--city": "city",
        "address--countryRegion": "state",
        "address--postalCode": "postal_code",
        "address--regionSubdivision1": "county",
        "countryRegion": "state",
        "regionSubdivision1": "county",
        "phoneNumber--phoneType": "phone_type",
        "phoneType": "phone_type",
        "phoneNumber--countryPhoneCode": "country_phone_code",
        "phoneNumber--phoneNumber": "phone",
        "phoneNumber--extension": "phone_extension",
        "phoneNumber": "phone",
        "extension": "phone_extension",
        "phone-sms-opt-in": "phone_sms_opt_in",
    }

    for source_key, target_key in key_mapping.items():
        if target_key not in normalized and source_key in normalized:
            normalized[target_key] = normalized[source_key]

    return normalized


class UserProfile(BaseModel):
    """User profile with structured data"""
    user_id: str
    full_name: str = Field(alias="name")  # Accept both 'name' and 'full_name'
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    password: Optional[str] = None  # In production, this should be hashed
    referral_source: Optional[str] = None
    preferred_name_opt_in: Optional[bool] = None
    preferred_name: Optional[str] = None
    phone: Optional[str] = None
    phone_type: Optional[str] = None
    country_phone_code: Optional[str] = None
    phone_extension: Optional[str] = None
    phone_sms_opt_in: Optional[bool] = None
    location: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website_url: Optional[str] = None
    twitter_url: Optional[str] = None
    workday_profile_url: Optional[str] = None
    pronouns: Optional[str] = None
    date_of_birth: Optional[str] = None
    current_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    skills: Optional[List[str]] = None
    education: Optional[List[Dict[str, Any]]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    preferred_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    employment_type_preferences: Optional[List[str]] = None
    willing_to_relocate: Optional[bool] = None
    willing_to_travel: Optional[bool] = None
    remote_preference: Optional[str] = None
    work_authorization: Optional[str] = None
    legally_authorized_to_work: Optional[bool] = None
    requires_visa_sponsorship: Optional[bool] = None
    master_resume_path: Optional[str] = None
    visa_status: Optional[str] = None
    notice_period: Optional[str] = None
    earliest_start_date: Optional[str] = None
    salary_expectation: Optional[str] = None
    desired_salary_min: Optional[float] = None
    desired_salary_max: Optional[float] = None
    desired_salary_currency: Optional[str] = None
    links: Optional[Dict[str, str]] = None
    equal_opportunity_gender: Optional[str] = None
    equal_opportunity_ethnicity: Optional[str] = None
    equal_opportunity_veteran_status: Optional[str] = None
    equal_opportunity_disability_status: Optional[str] = None
    data_consent: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        populate_by_name = True  # Allow both alias and field name
        by_alias = True  # Serialize using alias (return 'name' to frontend)


class CreateUserProfileRequest(BaseModel):
    """Request to create a new user profile"""
    full_name: str = Field(alias="name")  # Accept both 'name' and 'full_name'
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    password: Optional[str] = None
    referral_source: Optional[str] = None
    preferred_name_opt_in: Optional[bool] = None
    preferred_name: Optional[str] = None
    phone: Optional[str] = None
    phone_type: Optional[str] = None
    country_phone_code: Optional[str] = None
    phone_extension: Optional[str] = None
    phone_sms_opt_in: Optional[bool] = None
    location: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website_url: Optional[str] = None
    twitter_url: Optional[str] = None
    workday_profile_url: Optional[str] = None
    pronouns: Optional[str] = None
    date_of_birth: Optional[str] = None
    current_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    skills: Optional[List[str]] = None
    education: Optional[List[Dict[str, Any]]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    preferred_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    employment_type_preferences: Optional[List[str]] = None
    willing_to_relocate: Optional[bool] = None
    willing_to_travel: Optional[bool] = None
    remote_preference: Optional[str] = None
    work_authorization: Optional[str] = None
    legally_authorized_to_work: Optional[bool] = None
    requires_visa_sponsorship: Optional[bool] = None
    visa_status: Optional[str] = None
    notice_period: Optional[str] = None
    earliest_start_date: Optional[str] = None
    salary_expectation: Optional[str] = None
    desired_salary_min: Optional[float] = None
    desired_salary_max: Optional[float] = None
    desired_salary_currency: Optional[str] = None
    links: Optional[Dict[str, str]] = None
    equal_opportunity_gender: Optional[str] = None
    equal_opportunity_ethnicity: Optional[str] = None
    equal_opportunity_veteran_status: Optional[str] = None
    equal_opportunity_disability_status: Optional[str] = None
    data_consent: Optional[bool] = None
    
    class Config:
        populate_by_name = True  # Allow both alias and field name

    @model_validator(mode="before")
    @classmethod
    def normalize_password_key(cls, data: Any) -> Any:
        """Normalize common client payload key variants."""
        normalized = _normalize_profile_payload_keys(data)
        if not isinstance(normalized, dict):
            return normalized
        if "password" not in normalized and "passoword" in normalized:
            normalized["password"] = normalized["passoword"]
        if isinstance(normalized.get("links"), list) and len(normalized["links"]) == 0:
            normalized["links"] = None
        return normalized


class UpdateUserProfileRequest(BaseModel):
    """Request to update user profile - all fields optional"""
    full_name: Optional[str] = Field(None, alias="name")  # Accept both 'name' and 'full_name'
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    referral_source: Optional[str] = None
    preferred_name_opt_in: Optional[bool] = None
    preferred_name: Optional[str] = None
    phone: Optional[str] = None
    phone_type: Optional[str] = None
    country_phone_code: Optional[str] = None
    phone_extension: Optional[str] = None
    phone_sms_opt_in: Optional[bool] = None
    location: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website_url: Optional[str] = None
    twitter_url: Optional[str] = None
    workday_profile_url: Optional[str] = None
    pronouns: Optional[str] = None
    date_of_birth: Optional[str] = None
    current_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    skills: Optional[List[str]] = None
    education: Optional[List[Dict[str, Any]]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    preferred_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    employment_type_preferences: Optional[List[str]] = None
    willing_to_relocate: Optional[bool] = None
    willing_to_travel: Optional[bool] = None
    remote_preference: Optional[str] = None
    work_authorization: Optional[str] = None
    legally_authorized_to_work: Optional[bool] = None
    requires_visa_sponsorship: Optional[bool] = None
    visa_status: Optional[str] = None
    notice_period: Optional[str] = None
    earliest_start_date: Optional[str] = None
    salary_expectation: Optional[str] = None
    desired_salary_min: Optional[float] = None
    desired_salary_max: Optional[float] = None
    desired_salary_currency: Optional[str] = None
    links: Optional[Dict[str, str]] = None
    equal_opportunity_gender: Optional[str] = None
    equal_opportunity_ethnicity: Optional[str] = None
    equal_opportunity_veteran_status: Optional[str] = None
    equal_opportunity_disability_status: Optional[str] = None
    data_consent: Optional[bool] = None
    
    class Config:
        populate_by_name = True  # Allow both alias and field name
    master_resume_path: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_password_key(cls, data: Any) -> Any:
        """Normalize common client payload key variants."""
        normalized = _normalize_profile_payload_keys(data)
        if not isinstance(normalized, dict):
            return normalized
        if "password" not in normalized and "passoword" in normalized:
            normalized["password"] = normalized["passoword"]
        if isinstance(normalized.get("links"), list) and len(normalized["links"]) == 0:
            normalized["links"] = None
        return normalized


# ===== Logging & Analytics Models =====
class ApplicationLog(BaseModel):
    """Log entry for each application"""
    application_id: str
    user_id: str
    job_id: str
    company: str
    role: str
    resume_version: str
    answers_count: int
    status: ApplicationStatus
    submitted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


# ===== Request/Response Models =====
class AnalyzeJobRequest(BaseModel):
    """Request to analyze a job description"""
    job_description: JobDescription
    user_profile_id: Optional[str] = None


class TailorResumeRequest(BaseModel):
    """Request to tailor resume"""
    job_id: str
    user_id: str


class AnswerQuestionRequest(BaseModel):
    """Request to answer a single question"""
    question_context: QuestionContext
    user_id: str


class FillApplicationRequest(BaseModel):
    """Request to fill entire application"""
    application_form: ApplicationForm
    job_description: JobDescription
    user_id: str
    auto_submit: bool = False


class FillApplicationFormRequest(BaseModel):
    """Browser request for extracted form fields and optional user profile data."""
    form_fields: List[FormField]
    user_id: str
    job_id: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None


class FillApplicationFormResponse(BaseModel):
    """Answer bundle returned to the client"""
    answers: List[QuestionAnswer]
    overall_confidence: float
    warnings: Optional[List[str]] = None


class ApproveApplicationRequest(BaseModel):
    """Request to approve and submit application"""
    application_id: str
    user_id: str
    edited_fields: Optional[List[FilledField]] = None


# ===== Error Models =====
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
