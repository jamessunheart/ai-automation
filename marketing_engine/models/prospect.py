"""Data models for prospects and campaigns"""

from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
from pydantic import BaseModel, EmailStr


class ProspectStatus(str, Enum):
    """Status of prospect in the pipeline"""
    NEW = "new"
    RESEARCHING = "researching"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    REPLIED = "replied"
    MEETING_BOOKED = "meeting_booked"
    PROPOSAL_SENT = "proposal_sent"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    UNRESPONSIVE = "unresponsive"


class ProspectScore(BaseModel):
    """AI-generated prospect scoring"""
    total_score: float  # 0-100
    fit_score: float  # How well they match ICP
    intent_score: float  # Likelihood they need solution
    timing_score: float  # Likelihood they'll buy soon
    authority_score: float  # Decision-making power
    budget_score: float  # Estimated budget fit
    reasoning: str  # AI explanation of score


class Prospect(BaseModel):
    """Prospect/lead data model"""
    id: Optional[str] = None

    # Basic info
    first_name: str
    last_name: str
    email: EmailStr
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None

    # Company info
    company_name: str
    company_size: Optional[str] = None  # "50-100", "100-250", etc.
    company_industry: Optional[str] = None
    company_website: Optional[str] = None

    # Job info
    job_title: str
    job_function: Optional[str] = None  # "Operations", "Engineering", etc.
    seniority_level: Optional[str] = None  # "VP", "Director", "C-Level"

    # Enrichment data
    pain_points: List[str] = []
    technologies_used: List[str] = []
    recent_news: List[str] = []
    funding_stage: Optional[str] = None

    # Scoring
    score: Optional[ProspectScore] = None

    # Outreach tracking
    status: ProspectStatus = ProspectStatus.NEW
    outreach_attempts: int = 0
    last_contacted: Optional[datetime] = None
    last_replied: Optional[datetime] = None

    # Campaign tracking
    campaign_id: Optional[str] = None
    source: str  # "linkedin", "apollo", "manual", etc.

    # Conversation history
    emails_sent: List[Dict] = []  # {timestamp, subject, body, template_id}
    emails_received: List[Dict] = []  # {timestamp, subject, body}

    # Meeting info
    meeting_scheduled: Optional[datetime] = None
    meeting_notes: Optional[str] = None

    # Metadata
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    tags: List[str] = []
    custom_fields: Dict = {}

    # Human review flags
    needs_review: bool = False
    review_reason: Optional[str] = None
    approved_for_outreach: bool = False
    approved_by: Optional[str] = None


class Campaign(BaseModel):
    """Outreach campaign configuration"""
    id: Optional[str] = None
    name: str
    description: str

    # Targeting
    target_industries: List[str] = []
    target_company_sizes: List[str] = []
    target_job_titles: List[str] = []
    target_seniority: List[str] = []

    # Messaging
    value_proposition: str
    pain_points_addressed: List[str] = []
    email_sequence_templates: List[str] = []  # Template IDs

    # Settings
    daily_outreach_limit: int = 50
    follow_up_delays_days: List[int] = [3, 7, 14]  # Days between follow-ups

    # Status
    active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Metrics
    prospects_added: int = 0
    emails_sent: int = 0
    replies_received: int = 0
    meetings_booked: int = 0
    deals_closed: int = 0

    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()


class EmailTemplate(BaseModel):
    """Email template with personalization variables"""
    id: Optional[str] = None
    name: str
    subject: str  # Can include {{variables}}
    body: str  # Can include {{variables}}

    # Sequence info
    sequence_position: int  # 1 = initial, 2 = follow-up 1, etc.
    template_type: str  # "initial", "follow_up", "value_add", "final"

    # Personalization variables available
    # {{first_name}}, {{company_name}}, {{job_title}}, {{pain_point}}, etc.

    # Performance tracking
    sent_count: int = 0
    open_count: int = 0
    reply_count: int = 0

    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
