"""Outreach AI - Autonomous email personalization and sending"""

import os
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime
import anthropic

from ..models.prospect import Prospect, EmailTemplate, ProspectStatus
from ..services.email_service import get_email_service

logger = logging.getLogger(__name__)


class OutreachAI:
    """
    Outreach AI Agent - Personalizes and sends outreach emails

    Capabilities:
    - Generate hyper-personalized email copy
    - Adapt messaging based on prospect score/profile
    - A/B test subject lines and messaging
    - Handle email sequencing and follow-ups
    - Track engagement and optimize
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize Outreach AI with Claude API"""
        self.api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        self.email_service = get_email_service()

        if not self.client:
            logger.warning("⚠️  ANTHROPIC_API_KEY not set. Outreach AI will run in simulation mode.")


    async def personalize_email(
        self,
        prospect: Prospect,
        template: EmailTemplate,
        campaign: Dict
    ) -> Dict[str, str]:
        """
        Generate highly personalized email for a specific prospect

        Returns:
            Dict with 'subject' and 'body' keys containing personalized content
        """

        logger.info(f"✍️  Personalizing email for {prospect.first_name} {prospect.last_name}")

        if not self.client:
            return self._simulate_personalization(prospect, template)

        try:
            # Build context for personalization
            context = f"""
Prospect Information:
- Name: {prospect.first_name} {prospect.last_name}
- Title: {prospect.job_title}
- Company: {prospect.company_name} ({prospect.company_size} employees)
- Industry: {prospect.company_industry}
- Pain Points: {', '.join(prospect.pain_points)}
- Prospect Score: {prospect.score.total_score if prospect.score else 'Not scored'}/100

Campaign Information:
- Value Proposition: {campaign.get('value_proposition', '')}
- Pain Points We Address: {', '.join(campaign.get('pain_points_addressed', []))}

Email Template:
- Type: {template.template_type}
- Subject: {template.subject}
- Body: {template.body}

Your Task:
Create a highly personalized email that:
1. Uses the prospect's specific pain points and context
2. Speaks directly to their role and challenges
3. Makes the value proposition relevant to their situation
4. Feels natural and conversational, not templated
5. Includes specific numbers/ROI when relevant
6. Has a clear, low-friction call to action

Important:
- Keep it concise (under 150 words)
- Use {{{{first_name}}}}, {{{{company_name}}}} etc as placeholders for template variables
- Make subject line compelling and specific (not generic)
- Avoid marketing clichés and buzzwords
- Sound like a real human reaching out

Return JSON:
{{
  "subject": "personalized subject line",
  "body": "personalized email body"
}}"""

            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1500,
                messages=[{"role": "user", "content": context}]
            )

            response_text = message.content[0].text

            # Parse response
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                personalized = json.loads(json_str)

                logger.info(f"✅ Generated personalized email: \"{personalized.get('subject', '')[:50]}...\"")

                return personalized

            except json.JSONDecodeError:
                logger.warning("⚠️  Could not parse personalization JSON, using template")
                return self._simulate_personalization(prospect, template)

        except Exception as e:
            logger.error(f"❌ Personalization failed: {e}")
            return self._simulate_personalization(prospect, template)


    async def send_outreach_email(
        self,
        prospect: Prospect,
        personalized_email: Dict[str, str],
        campaign: Dict,
        dry_run: bool = False
    ) -> Dict:
        """
        Send personalized outreach email to prospect

        Args:
            prospect: Prospect to contact
            personalized_email: Dict with 'subject' and 'body'
            campaign: Campaign configuration
            dry_run: If True, don't actually send (for testing)

        Returns:
            Dict with send result
        """

        # Replace template variables
        subject = self._replace_variables(personalized_email['subject'], prospect)
        body_html = self._replace_variables(personalized_email['body'], prospect)

        # Convert to HTML format
        body_html = self._text_to_html(body_html)

        logger.info(f"📧 {'[DRY RUN] ' if dry_run else ''}Sending to {prospect.email}")
        logger.info(f"   Subject: {subject}")

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "prospect_id": prospect.id,
                "subject": subject,
                "preview": body_html[:200]
            }

        # Send via email service
        result = self.email_service.send_email(
            to_email=prospect.email,
            to_name=f"{prospect.first_name} {prospect.last_name}",
            subject=subject,
            body_html=body_html,
            custom_args={
                "prospect_id": prospect.id,
                "campaign_id": campaign.get("id"),
                "sequence_position": "1"
            }
        )

        if result.get("success"):
            # Update prospect
            prospect.status = ProspectStatus.CONTACTED
            prospect.outreach_attempts += 1
            prospect.last_contacted = datetime.utcnow()
            prospect.emails_sent.append({
                "timestamp": datetime.utcnow().isoformat(),
                "subject": subject,
                "body": body_html,
                "message_id": result.get("message_id")
            })

            logger.info(f"✅ Email sent successfully to {prospect.email}")

        return result


    async def send_bulk_outreach(
        self,
        prospects: List[Prospect],
        template: EmailTemplate,
        campaign: Dict,
        daily_limit: int = 50,
        dry_run: bool = False
    ) -> Dict:
        """
        Send personalized outreach to multiple prospects with rate limiting

        Returns:
            Dict with bulk send statistics
        """

        logger.info(f"📧 {'[DRY RUN] ' if dry_run else ''}Starting bulk outreach to {len(prospects)} prospects")

        results = {
            "total": len(prospects),
            "personalized": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }

        for i, prospect in enumerate(prospects):
            # Check daily limit
            if i >= daily_limit:
                results["skipped"] = len(prospects) - i
                logger.warning(f"⚠️  Daily limit reached ({daily_limit}), stopping")
                break

            try:
                # Personalize email
                personalized = await self.personalize_email(prospect, template, campaign)
                results["personalized"] += 1

                # Send email
                send_result = await self.send_outreach_email(
                    prospect=prospect,
                    personalized_email=personalized,
                    campaign=campaign,
                    dry_run=dry_run
                )

                if send_result.get("success"):
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "prospect": prospect.email,
                        "error": send_result.get("error", "Unknown error")
                    })

                # Delay between sends (2 seconds)
                if not dry_run and i < len(prospects) - 1:
                    import asyncio
                    await asyncio.sleep(2)

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "prospect": prospect.email,
                    "error": str(e)
                })
                logger.error(f"❌ Failed to send to {prospect.email}: {e}")

        logger.info(f"📊 Bulk outreach complete: {results['sent']}/{results['total']} sent")

        return results


    def _replace_variables(self, text: str, prospect: Prospect) -> str:
        """Replace template variables with prospect data"""

        variables = {
            "first_name": prospect.first_name,
            "last_name": prospect.last_name,
            "full_name": f"{prospect.first_name} {prospect.last_name}",
            "company_name": prospect.company_name,
            "company_size": prospect.company_size or "your size",
            "job_title": prospect.job_title,
            "industry": prospect.company_industry or "your industry",
            "pain_point": prospect.pain_points[0] if prospect.pain_points else "operational challenges"
        }

        result = text
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", value)

        return result


    def _text_to_html(self, text: str) -> str:
        """Convert plain text to simple HTML"""

        # Split into paragraphs
        paragraphs = text.split('\n\n')

        html_parts = ['<div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">']

        for para in paragraphs:
            if para.strip():
                # Handle line breaks within paragraphs
                para_html = para.replace('\n', '<br>')
                html_parts.append(f'<p>{para_html}</p>')

        # Add signature
        html_parts.append("""
<p>Best,<br>
James<br>
<strong>Full Potential AI</strong><br>
<a href="https://fullpotential.com/ai">fullpotential.com/ai</a></p>
</div>
""")

        return '\n'.join(html_parts)


    def _simulate_personalization(self, prospect: Prospect, template: EmailTemplate) -> Dict[str, str]:
        """Simulate personalization when API not available"""

        # Simple template variable replacement
        subject = template.subject.replace("{{first_name}}", prospect.first_name)
        subject = subject.replace("{{company_name}}", prospect.company_name)

        body = template.body
        body = body.replace("{{first_name}}", prospect.first_name)
        body = body.replace("{{company_name}}", prospect.company_name)
        body = body.replace("{{job_title}}", prospect.job_title)

        if prospect.pain_points:
            pain_point = prospect.pain_points[0]
            body = body.replace("{{pain_point}}", pain_point)

        logger.info(f"✅ [SIMULATED] Personalized email for {prospect.first_name}")

        return {
            "subject": subject,
            "body": body
        }


# Global instance
_outreach_ai = None


def get_outreach_ai() -> OutreachAI:
    """Get or create global Outreach AI instance"""
    global _outreach_ai
    if _outreach_ai is None:
        _outreach_ai = OutreachAI()
    return _outreach_ai
