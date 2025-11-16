"""FastAPI endpoints for AI Marketing Engine"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime

from .models.prospect import Prospect, Campaign, EmailTemplate, ProspectStatus
from .agents.orchestrator import get_orchestrator
from .agents.research_ai import get_research_ai
from .agents.outreach_ai import get_outreach_ai
from .agents.conversation_ai import get_conversation_ai

# Create API router
router = APIRouter(prefix="/api/marketing", tags=["marketing"])

# Get orchestrator instance
orchestrator = get_orchestrator()


@router.get("/health")
async def health():
    """Health check for marketing engine"""
    return {
        "status": "healthy",
        "service": "ai-marketing-engine",
        "version": "1.0.0",
        "components": {
            "research_ai": "active",
            "outreach_ai": "active",
            "conversation_ai": "active",
            "orchestrator": "active"
        }
    }


@router.post("/campaigns")
async def create_campaign(campaign: Campaign):
    """Create a new outreach campaign"""

    # Generate campaign ID
    campaign.id = f"campaign_{len(orchestrator.campaigns) + 1}"
    campaign.created_at = datetime.utcnow()

    # Store campaign
    orchestrator.campaigns[campaign.id] = campaign

    return {
        "success": True,
        "campaign_id": campaign.id,
        "campaign": campaign
    }


@router.get("/campaigns")
async def list_campaigns():
    """List all campaigns"""
    return {
        "campaigns": list(orchestrator.campaigns.values())
    }


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get campaign details"""

    campaign = orchestrator.campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return campaign


@router.post("/campaigns/{campaign_id}/run-workflow")
async def run_campaign_workflow(campaign_id: str, background_tasks: BackgroundTasks):
    """
    Start the daily automation workflow for a campaign

    This runs the complete 6 AM - 6 PM automation cycle
    """

    campaign = orchestrator.campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Run workflow in background
    background_tasks.add_task(orchestrator.run_daily_workflow, campaign_id)

    return {
        "success": True,
        "message": f"Daily workflow started for campaign: {campaign.name}",
        "campaign_id": campaign_id
    }


@router.get("/campaigns/{campaign_id}/prospects")
async def get_campaign_prospects(
    campaign_id: str,
    status: Optional[ProspectStatus] = None,
    limit: int = 100
):
    """Get prospects for a campaign, optionally filtered by status"""

    prospects = [
        p for p in orchestrator.prospects.values()
        if p.campaign_id == campaign_id
    ]

    # Filter by status if provided
    if status:
        prospects = [p for p in prospects if p.status == status]

    # Limit results
    prospects = prospects[:limit]

    return {
        "campaign_id": campaign_id,
        "total": len(prospects),
        "prospects": prospects
    }


@router.get("/prospects/pending-approval")
async def get_pending_approvals():
    """Get prospects awaiting human approval"""

    return {
        "total": len(orchestrator.pending_approvals),
        "prospects": orchestrator.pending_approvals
    }


@router.post("/prospects/approve")
async def approve_prospects(prospect_ids: List[str], approved_by: str = "human"):
    """
    Approve prospects for outreach

    This is the human touchpoint where the Campaign Manager
    reviews and approves AI-generated prospect list (15 min/day)
    """

    count = await orchestrator.approve_prospects(prospect_ids, approved_by)

    return {
        "success": True,
        "approved_count": count,
        "message": f"Approved {count} prospects for outreach"
    }


@router.get("/prospects/{prospect_id}")
async def get_prospect(prospect_id: str):
    """Get detailed prospect information"""

    prospect = orchestrator.prospects.get(prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    return prospect


@router.post("/outreach/personalize")
async def personalize_email(
    prospect_id: str,
    template_id: str,
    campaign_id: str
):
    """
    Generate personalized email for a prospect

    Useful for previewing before sending
    """

    prospect = orchestrator.prospects.get(prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    template = orchestrator.templates.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    campaign = orchestrator.campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    outreach_ai = get_outreach_ai()
    personalized = await outreach_ai.personalize_email(prospect, template, campaign.__dict__)

    return {
        "prospect_id": prospect_id,
        "template_id": template_id,
        "personalized_email": personalized
    }


@router.post("/outreach/send")
async def send_outreach_email(
    prospect_id: str,
    subject: str,
    body: str,
    campaign_id: str,
    dry_run: bool = False
):
    """Send personalized outreach email to prospect"""

    prospect = orchestrator.prospects.get(prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    campaign = orchestrator.campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    outreach_ai = get_outreach_ai()
    result = await outreach_ai.send_outreach_email(
        prospect=prospect,
        personalized_email={"subject": subject, "body": body},
        campaign=campaign.__dict__,
        dry_run=dry_run
    )

    return result


@router.get("/replies/pending")
async def get_pending_replies():
    """
    Get replies awaiting human review

    These are high-value or complex replies that need human attention
    """

    return {
        "total": len(orchestrator.pending_replies),
        "replies": orchestrator.pending_replies
    }


@router.post("/replies/process")
async def process_reply(
    prospect_id: str,
    reply_text: str,
    reply_subject: str,
    campaign_id: str,
    auto_respond: bool = False
):
    """
    Process an incoming email reply

    - Analyzes the reply
    - Qualifies the prospect
    - Drafts response
    - Optionally auto-sends if simple query
    """

    prospect = orchestrator.prospects.get(prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    campaign = orchestrator.campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    conversation_ai = get_conversation_ai()

    reply_email = {
        "subject": reply_subject,
        "body": reply_text,
        "timestamp": datetime.utcnow().isoformat()
    }

    result = await conversation_ai.handle_reply(
        prospect=prospect,
        reply_email=reply_email,
        campaign=campaign.__dict__,
        auto_respond=auto_respond
    )

    return result


@router.get("/analytics/dashboard")
async def get_analytics_dashboard(campaign_id: Optional[str] = None):
    """
    Get analytics dashboard data

    Overall stats or campaign-specific if campaign_id provided
    """

    prospects = list(orchestrator.prospects.values())

    if campaign_id:
        prospects = [p for p in prospects if p.campaign_id == campaign_id]

    # Calculate metrics
    total_prospects = len(prospects)
    total_contacted = len([p for p in prospects if p.status in [
        ProspectStatus.CONTACTED,
        ProspectStatus.REPLIED,
        ProspectStatus.QUALIFIED,
        ProspectStatus.MEETING_BOOKED
    ]])
    total_replied = len([p for p in prospects if p.status in [
        ProspectStatus.REPLIED,
        ProspectStatus.QUALIFIED,
        ProspectStatus.MEETING_BOOKED
    ]])
    total_meetings = len([p for p in prospects if p.status == ProspectStatus.MEETING_BOOKED])
    total_closed_won = len([p for p in prospects if p.status == ProspectStatus.CLOSED_WON])

    # Calculate rates
    reply_rate = (total_replied / total_contacted * 100) if total_contacted > 0 else 0
    meeting_rate = (total_meetings / total_replied * 100) if total_replied > 0 else 0

    return {
        "campaign_id": campaign_id,
        "metrics": {
            "total_prospects": total_prospects,
            "total_contacted": total_contacted,
            "total_replied": total_replied,
            "total_meetings_booked": total_meetings,
            "total_closed_won": total_closed_won,
            "reply_rate": round(reply_rate, 2),
            "meeting_rate": round(meeting_rate, 2)
        },
        "by_status": {
            "new": len([p for p in prospects if p.status == ProspectStatus.NEW]),
            "qualified": len([p for p in prospects if p.status == ProspectStatus.QUALIFIED]),
            "contacted": len([p for p in prospects if p.status == ProspectStatus.CONTACTED]),
            "replied": len([p for p in prospects if p.status == ProspectStatus.REPLIED]),
            "meeting_booked": total_meetings,
            "closed_won": total_closed_won,
            "closed_lost": len([p for p in prospects if p.status == ProspectStatus.CLOSED_LOST])
        }
    }


@router.post("/templates")
async def create_template(template: EmailTemplate):
    """Create a new email template"""

    template.id = f"template_{len(orchestrator.templates) + 1}"
    template.created_at = datetime.utcnow()

    orchestrator.templates[template.id] = template

    return {
        "success": True,
        "template_id": template.id,
        "template": template
    }


@router.get("/templates")
async def list_templates():
    """List all email templates"""

    return {
        "templates": list(orchestrator.templates.values())
    }


@router.get("/daily-summary/{campaign_id}")
async def get_daily_summary(campaign_id: str):
    """Get daily summary report for a campaign"""

    campaign = orchestrator.campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    summary = await orchestrator.evening_summary(campaign)

    return summary
