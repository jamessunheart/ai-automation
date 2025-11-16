"""Orchestrator AI - Master coordinator for the marketing automation system"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, time
import asyncio

from ..models.prospect import Prospect, Campaign, EmailTemplate, ProspectStatus
from .research_ai import get_research_ai
from .outreach_ai import get_outreach_ai
from .conversation_ai import get_conversation_ai

logger = logging.getLogger(__name__)


class OrchestratorAI:
    """
    Orchestrator AI - Coordinates all marketing automation agents

    Daily Workflow:
    6:00 AM - Research AI finds new prospects
    7:00 AM - Score and enrich prospects
    8:00 AM - Generate approval queue for human
    9:00 AM - Human approves prospects (15 min)
    10:00 AM - Personalize emails for approved prospects
    11:00 AM - Send morning batch (25 emails)
    12:00 PM - Check for replies, draft responses
    2:00 PM - Send afternoon batch (25 emails)
    4:00 PM - Process replies, update CRM
    5:00 PM - Generate daily report
    6:00 PM - Prepare next day's prospects

    Human Touchpoints:
    - Morning: Approve prospect list (15 min)
    - Afternoon: Review drafts for high-value replies (15 min)
    - Throughout day: Handle calls, close deals (2-4 hours)
    """

    def __init__(self):
        """Initialize orchestrator with all AI agents"""
        self.research_ai = get_research_ai()
        self.outreach_ai = get_outreach_ai()
        self.conversation_ai = get_conversation_ai()

        # In-memory storage (in production, use database)
        self.prospects: Dict[str, Prospect] = {}
        self.campaigns: Dict[str, Campaign] = {}
        self.templates: Dict[str, EmailTemplate] = {}
        self.pending_approvals: List[Prospect] = []
        self.pending_replies: List[Dict] = []

        logger.info("🎯 Orchestrator AI initialized")


    async def run_daily_workflow(self, campaign_id: str):
        """Execute the complete daily automation workflow"""

        logger.info(f"🚀 Starting daily workflow for campaign: {campaign_id}")

        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            logger.error(f"❌ Campaign {campaign_id} not found")
            return

        # Execute workflow steps
        await self.morning_research(campaign)
        await self.morning_approval_prep(campaign)
        # Human approval happens here (9 AM)
        await self.morning_outreach_batch(campaign)
        await self.check_and_process_replies(campaign)
        await self.afternoon_outreach_batch(campaign)
        await self.evening_summary(campaign)

        logger.info(f"✅ Daily workflow complete for campaign: {campaign_id}")


    async def morning_research(self, campaign: Campaign):
        """
        6:00-8:00 AM: Find and qualify new prospects

        - Find 20 new prospects matching ICP
        - Enrich with company data and pain points
        - Score each prospect
        - Flag top prospects for approval
        """

        logger.info("🔍 [6:00 AM] Starting morning research...")

        # Find new prospects
        daily_target = campaign.daily_outreach_limit
        prospects = await self.research_ai.find_prospects(campaign.__dict__, limit=daily_target)

        # Enrich and score each prospect
        for prospect in prospects:
            # Enrich
            prospect = await self.research_ai.enrich_prospect(prospect)

            # Score
            score = await self.research_ai.score_prospect(prospect, campaign.__dict__)
            prospect.score = score

            # Store prospect
            prospect.id = f"prospect_{len(self.prospects) + 1}"
            self.prospects[prospect.id] = prospect

            logger.info(f"  ✅ {prospect.first_name} {prospect.last_name} - Score: {score.total_score}/100")

        logger.info(f"✅ Research complete - Found and scored {len(prospects)} prospects")

        return prospects


    async def morning_approval_prep(self, campaign: Campaign):
        """
        8:00-9:00 AM: Prepare prospect approval queue for human

        - Sort prospects by score
        - Create approval list with key details
        - Generate recommended outreach messages
        """

        logger.info("📋 [8:00 AM] Preparing approval queue...")

        # Get today's prospects that need approval
        new_prospects = [
            p for p in self.prospects.values()
            if p.status == ProspectStatus.NEW
            and p.campaign_id == campaign.id
            and not p.approved_for_outreach
        ]

        # Sort by score
        new_prospects.sort(key=lambda p: p.score.total_score if p.score else 0, reverse=True)

        # Create approval queue
        self.pending_approvals = new_prospects

        logger.info(f"✅ Approval queue ready - {len(new_prospects)} prospects waiting for human review")

        return new_prospects


    async def approve_prospects(self, prospect_ids: List[str], approved_by: str = "human"):
        """
        Human approves prospects for outreach

        This is the 15-minute human touchpoint at 9 AM
        """

        logger.info(f"✅ [9:00 AM] Human approving {len(prospect_ids)} prospects...")

        approved_count = 0
        for prospect_id in prospect_ids:
            prospect = self.prospects.get(prospect_id)
            if prospect:
                prospect.approved_for_outreach = True
                prospect.approved_by = approved_by
                prospect.status = ProspectStatus.QUALIFIED
                approved_count += 1

                logger.info(f"  ✅ Approved: {prospect.first_name} {prospect.last_name}")

        logger.info(f"✅ Approved {approved_count} prospects for outreach")

        return approved_count


    async def morning_outreach_batch(self, campaign: Campaign):
        """
        10:00-11:00 AM: Personalize and send morning emails

        - Get approved prospects
        - Personalize each email
        - Send morning batch (25 emails)
        """

        logger.info("📧 [10:00 AM] Starting morning outreach batch...")

        # Get approved prospects
        approved = [
            p for p in self.prospects.values()
            if p.approved_for_outreach
            and p.status == ProspectStatus.QUALIFIED
            and p.outreach_attempts == 0
        ]

        # Limit to morning batch size
        morning_batch = approved[:25]

        if not morning_batch:
            logger.info("ℹ️  No approved prospects for morning batch")
            return

        # Get template (would be from database in production)
        template = list(self.templates.values())[0] if self.templates else self._create_default_template()

        # Send bulk outreach
        result = await self.outreach_ai.send_bulk_outreach(
            prospects=morning_batch,
            template=template,
            campaign=campaign.__dict__,
            daily_limit=25,
            dry_run=False  # Set to True for testing
        )

        logger.info(f"✅ Morning batch complete - {result['sent']} emails sent")

        return result


    async def check_and_process_replies(self, campaign: Campaign):
        """
        12:00-2:00 PM: Check inbox and process replies

        - Check for new replies
        - Analyze each reply
        - Draft responses
        - Auto-respond to simple queries
        - Escalate complex ones to human
        """

        logger.info("📨 [12:00 PM] Checking for replies...")

        # In production, this would check email inbox via IMAP/API
        # For now, simulate with any prospects who have replies

        prospects_with_replies = [
            p for p in self.prospects.values()
            if len(p.emails_received) > len(p.emails_sent)  # More received than sent = new reply
        ]

        for prospect in prospects_with_replies:
            # Get latest reply
            latest_reply = prospect.emails_received[-1]

            # Process the reply
            result = await self.conversation_ai.handle_reply(
                prospect=prospect,
                reply_email=latest_reply,
                campaign=campaign.__dict__,
                auto_respond=True  # Automatically respond to simple queries
            )

            action = result.get('action')

            if action == 'escalated_to_human':
                self.pending_replies.append({
                    "prospect": prospect,
                    "analysis": result.get('analysis'),
                    "draft_reply": result.get('draft_reply')
                })
                logger.info(f"  🚨 Escalated to human: {prospect.first_name} {prospect.last_name}")

            elif action == 'auto_replied':
                logger.info(f"  ✅ Auto-replied: {prospect.first_name} {prospect.last_name}")

        logger.info(f"✅ Reply processing complete - {len(prospects_with_replies)} replies handled")

        return prospects_with_replies


    async def afternoon_outreach_batch(self, campaign: Campaign):
        """
        2:00-3:00 PM: Send afternoon batch

        - Same as morning batch
        - Different prospects or follow-ups
        """

        logger.info("📧 [2:00 PM] Starting afternoon outreach batch...")

        # Get approved prospects not yet contacted
        approved = [
            p for p in self.prospects.values()
            if p.approved_for_outreach
            and p.status == ProspectStatus.QUALIFIED
            and p.outreach_attempts == 0
        ]

        afternoon_batch = approved[:25]

        if not afternoon_batch:
            logger.info("ℹ️  No prospects for afternoon batch")
            return

        template = list(self.templates.values())[0] if self.templates else self._create_default_template()

        result = await self.outreach_ai.send_bulk_outreach(
            prospects=afternoon_batch,
            template=template,
            campaign=campaign.__dict__,
            daily_limit=25,
            dry_run=False
        )

        logger.info(f"✅ Afternoon batch complete - {result['sent']} emails sent")

        return result


    async def evening_summary(self, campaign: Campaign):
        """
        5:00-6:00 PM: Generate daily summary report

        - Total prospects found
        - Emails sent
        - Replies received
        - Meetings booked
        - Revenue pipeline added
        """

        logger.info("📊 [5:00 PM] Generating daily summary...")

        # Calculate metrics
        total_prospects = len([p for p in self.prospects.values() if p.campaign_id == campaign.id])
        emails_sent_today = len([
            p for p in self.prospects.values()
            if p.campaign_id == campaign.id
            and p.last_contacted
            and p.last_contacted.date() == datetime.utcnow().date()
        ])
        replies_today = len([
            p for p in self.prospects.values()
            if p.campaign_id == campaign.id
            and p.last_replied
            and p.last_replied.date() == datetime.utcnow().date()
        ])
        meetings_booked = len([
            p for p in self.prospects.values()
            if p.campaign_id == campaign.id
            and p.status == ProspectStatus.MEETING_BOOKED
        ])

        summary = {
            "date": datetime.utcnow().date().isoformat(),
            "campaign": campaign.name,
            "metrics": {
                "prospects_found": total_prospects,
                "emails_sent": emails_sent_today,
                "replies_received": replies_today,
                "meetings_booked": meetings_booked,
                "pending_approvals": len(self.pending_approvals),
                "pending_human_replies": len(self.pending_replies)
            },
            "human_actions_needed": {
                "approve_prospects": len(self.pending_approvals) > 0,
                "review_replies": len(self.pending_replies) > 0
            }
        }

        logger.info(f"""
📊 Daily Summary Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Campaign: {campaign.name}
Date: {summary['date']}

Metrics:
  • Prospects Found: {summary['metrics']['prospects_found']}
  • Emails Sent: {summary['metrics']['emails_sent']}
  • Replies Received: {summary['metrics']['replies_received']}
  • Meetings Booked: {summary['metrics']['meetings_booked']}

Human Actions Needed:
  • Pending Approvals: {summary['metrics']['pending_approvals']}
  • Pending Reply Reviews: {summary['metrics']['pending_human_replies']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)

        return summary


    def _create_default_template(self) -> EmailTemplate:
        """Create default email template"""

        return EmailTemplate(
            id="template_1",
            name="Initial Outreach - E-Commerce",
            subject="Cut {{company_name}}'s support costs by 70%",
            body="""Hi {{first_name}},

I noticed {{company_name}} has been scaling in the {{industry}} space. Quick question: Are you currently spending $50k-$100k/year on customer support for repetitive tasks like order status, returns, and basic questions?

We help companies like yours reduce support costs by 70% through AI automation.

**Real numbers for a company your size:**
- Traditional support: 3 reps @ $60k = $180k/year
- AI automation: $84k/year for 24/7 coverage
- **Net savings: $96k/year**

Would a 15-minute call this week make sense to explore if this could work for {{company_name}}?""",
            sequence_position=1,
            template_type="initial"
        )


# Global instance
_orchestrator = None


def get_orchestrator() -> OrchestratorAI:
    """Get or create global Orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAI()
    return _orchestrator
