"""Conversation AI - Autonomous reply handling and qualification"""

import os
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime
import anthropic

from ..models.prospect import Prospect, ProspectStatus
from ..services.email_service import get_email_service

logger = logging.getLogger(__name__)


class ConversationAI:
    """
    Conversation AI Agent - Handles email replies and qualifies prospects

    Capabilities:
    - Analyze reply sentiment and intent
    - Qualify prospects (BANT: Budget, Authority, Need, Timing)
    - Draft contextual responses
    - Book discovery calls automatically
    - Escalate to humans when appropriate
    - Handle objections intelligently
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize Conversation AI with Claude API"""
        self.api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        self.email_service = get_email_service()

        if not self.client:
            logger.warning("⚠️  ANTHROPIC_API_KEY not set. Conversation AI will run in simulation mode.")


    async def analyze_reply(self, prospect: Prospect, reply_text: str) -> Dict:
        """
        Analyze email reply to determine intent and qualification

        Returns:
            Dict with analysis including:
            - sentiment: "positive", "neutral", "negative"
            - intent: "interested", "not_interested", "needs_info", "timing_issue", "objection"
            - qualification_score: 0-100
            - key_points: List of important points from reply
            - recommended_action: What to do next
            - needs_human: Boolean whether to escalate
        """

        logger.info(f"🔍 Analyzing reply from {prospect.first_name} {prospect.last_name}")

        if not self.client:
            return self._simulate_analysis(reply_text)

        try:
            prompt = f"""You are a B2B sales AI analyzing an email reply. Analyze this prospect's response and determine how to proceed.

Prospect Context:
- Name: {prospect.first_name} {prospect.last_name}
- Title: {prospect.job_title}
- Company: {prospect.company_name}
- Previous outreach: {prospect.outreach_attempts} emails sent
- Current status: {prospect.status}

Their Reply:
\"\"\"{reply_text}\"\"\"

Analyze this reply and provide:

1. Sentiment: positive, neutral, or negative
2. Intent: interested, not_interested, needs_info, timing_issue, objection, meeting_request
3. Qualification (BANT):
   - Budget: Do they have/mention budget? (0-100)
   - Authority: Are they a decision maker? (0-100)
   - Need: Do they clearly need our solution? (0-100)
   - Timing: Will they buy soon? (0-100)
4. Key Points: Extract 2-3 main points from their message
5. Recommended Action: What should we do next?
6. Needs Human: Should a human take over this conversation?

Return JSON:
{{
  "sentiment": "positive|neutral|negative",
  "intent": "interested|not_interested|needs_info|timing_issue|objection|meeting_request",
  "qualification": {{
    "budget_score": 0-100,
    "authority_score": 0-100,
    "need_score": 0-100,
    "timing_score": 0-100,
    "total_score": average of above
  }},
  "key_points": ["point 1", "point 2"],
  "recommended_action": "send_info|book_meeting|follow_up_later|close_lost|escalate_to_human",
  "needs_human": true|false,
  "reasoning": "Brief explanation of the analysis"
}}"""

            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse analysis
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                analysis = json.loads(json_str)

                logger.info(f"✅ Reply analyzed - Intent: {analysis.get('intent')}, Qualification: {analysis.get('qualification', {}).get('total_score', 0)}/100")

                return analysis

            except json.JSONDecodeError:
                logger.warning("⚠️  Could not parse analysis JSON")
                return self._simulate_analysis(reply_text)

        except Exception as e:
            logger.error(f"❌ Reply analysis failed: {e}")
            return self._simulate_analysis(reply_text)


    async def draft_reply(
        self,
        prospect: Prospect,
        their_message: str,
        analysis: Dict,
        campaign: Dict
    ) -> Dict[str, str]:
        """
        Draft contextual reply based on their message and analysis

        Returns:
            Dict with 'subject' and 'body' for reply email
        """

        logger.info(f"✍️  Drafting reply for {prospect.first_name} {prospect.last_name}")

        if not self.client:
            return self._simulate_reply_draft(analysis)

        try:
            prompt = f"""You are a B2B sales AI drafting a reply email. Write a natural, helpful response.

Prospect Context:
- Name: {prospect.first_name} {prospect.last_name}
- Title: {prospect.job_title}
- Company: {prospect.company_name}
- Their Intent: {analysis.get('intent')}
- Their Key Points: {', '.join(analysis.get('key_points', []))}

Their Message:
\"\"\"{their_message}\"\"\"

Campaign Context:
- Value Proposition: {campaign.get('value_proposition', '')}
- Pain Points We Address: {', '.join(campaign.get('pain_points_addressed', []))}

Based on their intent ({analysis.get('intent')}), write an appropriate reply that:

1. If INTERESTED/MEETING_REQUEST:
   - Acknowledge their interest
   - Propose a specific meeting time (suggest 2-3 options)
   - Include calendar link
   - Keep it short and action-oriented

2. If NEEDS_INFO:
   - Address their specific questions
   - Provide relevant information/case studies
   - Suggest a brief call to discuss details
   - Soft call to action

3. If TIMING_ISSUE:
   - Acknowledge timing concerns
   - Ask when would be better to follow up
   - Offer to send helpful resources in meantime
   - Stay warm without being pushy

4. If OBJECTION:
   - Acknowledge their concern
   - Address objection briefly with value/proof
   - Offer to discuss on a quick call
   - Respectful persistence

Tone:
- Helpful and consultative, not salesy
- Brief (under 100 words)
- Natural and conversational
- Professional but friendly

Return JSON:
{{
  "subject": "Re: [their subject or relevant topic]",
  "body": "email body text"
}}"""

            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse draft
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                draft = json.loads(json_str)

                logger.info(f"✅ Reply drafted: \"{draft.get('subject', '')[:50]}...\"")

                return draft

            except json.JSONDecodeError:
                logger.warning("⚠️  Could not parse draft JSON")
                return self._simulate_reply_draft(analysis)

        except Exception as e:
            logger.error(f"❌ Reply drafting failed: {e}")
            return self._simulate_reply_draft(analysis)


    async def handle_reply(
        self,
        prospect: Prospect,
        reply_email: Dict,
        campaign: Dict,
        auto_respond: bool = False
    ) -> Dict:
        """
        Process incoming email reply end-to-end

        Args:
            prospect: Prospect who replied
            reply_email: Dict with 'subject', 'body', 'timestamp'
            campaign: Campaign configuration
            auto_respond: If True, automatically send drafted response

        Returns:
            Dict with analysis, draft reply, and action taken
        """

        logger.info(f"📨 Handling reply from {prospect.email}")

        # Store the reply
        prospect.emails_received.append(reply_email)
        prospect.last_replied = datetime.fromisoformat(reply_email.get('timestamp', datetime.utcnow().isoformat()))
        prospect.status = ProspectStatus.REPLIED

        # Analyze the reply
        analysis = await self.analyze_reply(prospect, reply_email['body'])

        # Draft response
        draft_reply = await self.draft_reply(prospect, reply_email['body'], analysis, campaign)

        # Determine if human should take over
        if analysis.get('needs_human', False):
            logger.info(f"🚨 Escalating to human - {analysis.get('reasoning', '')}")
            prospect.needs_review = True
            prospect.review_reason = f"Reply analysis: {analysis.get('reasoning', 'Complex response')}"

            return {
                "analysis": analysis,
                "draft_reply": draft_reply,
                "action": "escalated_to_human",
                "auto_sent": False
            }

        # Update qualification if they're qualified
        qual_score = analysis.get('qualification', {}).get('total_score', 0)
        if qual_score >= 70:
            prospect.status = ProspectStatus.QUALIFIED

        # Update status based on intent
        intent = analysis.get('intent')
        if intent == 'meeting_request' or analysis.get('recommended_action') == 'book_meeting':
            prospect.status = ProspectStatus.MEETING_BOOKED

        elif intent == 'not_interested':
            prospect.status = ProspectStatus.CLOSED_LOST

        # Auto-respond if enabled
        if auto_respond and not analysis.get('needs_human', False):
            # Send the drafted reply
            send_result = self.email_service.send_email(
                to_email=prospect.email,
                to_name=f"{prospect.first_name} {prospect.last_name}",
                subject=draft_reply['subject'],
                body_html=self._text_to_html(draft_reply['body']),
                custom_args={
                    "prospect_id": prospect.id,
                    "campaign_id": campaign.get("id"),
                    "type": "reply"
                }
            )

            if send_result.get('success'):
                prospect.emails_sent.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "subject": draft_reply['subject'],
                    "body": draft_reply['body'],
                    "message_id": send_result.get("message_id"),
                    "type": "auto_reply"
                })

                logger.info(f"✅ Auto-reply sent to {prospect.email}")

                return {
                    "analysis": analysis,
                    "draft_reply": draft_reply,
                    "action": "auto_replied",
                    "auto_sent": True,
                    "send_result": send_result
                }

        # If not auto-responding, return draft for human approval
        return {
            "analysis": analysis,
            "draft_reply": draft_reply,
            "action": "draft_ready",
            "auto_sent": False
        }


    def _text_to_html(self, text: str) -> str:
        """Convert plain text to HTML"""
        paragraphs = text.split('\n\n')
        html_parts = ['<div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">']

        for para in paragraphs:
            if para.strip():
                para_html = para.replace('\n', '<br>')
                html_parts.append(f'<p>{para_html}</p>')

        html_parts.append("""
<p>Best,<br>
James<br>
<strong>Full Potential AI</strong><br>
<a href="https://fullpotential.com/ai">fullpotential.com/ai</a></p>
</div>
""")

        return '\n'.join(html_parts)


    def _simulate_analysis(self, reply_text: str) -> Dict:
        """Simulate analysis when API not available"""

        # Simple keyword-based analysis
        text_lower = reply_text.lower()

        if any(word in text_lower for word in ['interested', 'yes', 'call', 'meeting', 'sounds good']):
            sentiment = "positive"
            intent = "interested"
            qual_score = 75
        elif any(word in text_lower for word in ['not interested', 'no thanks', 'remove']):
            sentiment = "negative"
            intent = "not_interested"
            qual_score = 0
        elif any(word in text_lower for word in ['more info', 'tell me', 'how does', 'pricing']):
            sentiment = "neutral"
            intent = "needs_info"
            qual_score = 60
        else:
            sentiment = "neutral"
            intent = "needs_info"
            qual_score = 50

        return {
            "sentiment": sentiment,
            "intent": intent,
            "qualification": {
                "budget_score": qual_score,
                "authority_score": 70,
                "need_score": qual_score,
                "timing_score": qual_score,
                "total_score": qual_score
            },
            "key_points": ["Prospect replied to outreach"],
            "recommended_action": "send_info" if intent == "needs_info" else "book_meeting",
            "needs_human": intent == "interested" or qual_score >= 75,
            "reasoning": f"Simulated analysis - detected {intent}"
        }


    def _simulate_reply_draft(self, analysis: Dict) -> Dict[str, str]:
        """Simulate reply drafting when API not available"""

        intent = analysis.get('intent')

        if intent == 'interested':
            return {
                "subject": "Re: AI Automation - Let's Schedule a Call",
                "body": "Great to hear from you! I'd love to discuss how AI automation could work for {{company_name}}.\n\nHow does a 15-minute call work this week? I'm available:\n- Tuesday 2-4pm EST\n- Wednesday 10am-12pm EST\n- Thursday 3-5pm EST\n\nLet me know what works best for you."
            }
        else:
            return {
                "subject": "Re: AI Automation Info",
                "body": "Thanks for your reply! I'd be happy to share more details.\n\nHere's a quick overview of how we help companies like {{company_name}}:\n- Automate repetitive workflows 24/7\n- Reduce operational costs by 60-80%\n- Deploy in 2-4 weeks\n\nWould a brief call work to discuss your specific situation?"
            }


# Global instance
_conversation_ai = None


def get_conversation_ai() -> ConversationAI:
    """Get or create global Conversation AI instance"""
    global _conversation_ai
    if _conversation_ai is None:
        _conversation_ai = ConversationAI()
    return _conversation_ai
