"""Research AI - Autonomous prospect finding and qualification"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import anthropic

from ..models.prospect import Prospect, ProspectScore, ProspectStatus

logger = logging.getLogger(__name__)


class ResearchAI:
    """
    Research AI Agent - Finds and qualifies prospects

    Capabilities:
    - Search for prospects matching ICP (Ideal Customer Profile)
    - Enrich prospect data (company info, tech stack, pain points)
    - Score prospects for outreach priority
    - Identify optimal timing and messaging angles
    - Flag prospects for human review when needed
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize Research AI with Claude API"""
        self.api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None

        if not self.client:
            logger.warning("⚠️  ANTHROPIC_API_KEY not set. Research AI will run in simulation mode.")


    async def find_prospects(
        self,
        campaign: Dict,
        limit: int = 20
    ) -> List[Prospect]:
        """
        Find prospects matching campaign criteria

        In production, this would:
        - Query LinkedIn Sales Navigator API
        - Search Apollo.io/ZoomInfo database
        - Scrape company websites for contact info
        - Use Hunter.io for email finding

        For now, we'll generate sample prospects based on OUTREACH_READY_TO_EXECUTE.md
        """

        logger.info(f"🔍 Finding {limit} prospects for campaign: {campaign.get('name')}")

        # In production, integrate with:
        # - LinkedIn Sales Navigator API
        # - Apollo.io API
        # - ZoomInfo API
        # - Hunter.io for email finding

        # For demo, return structured sample prospects
        sample_prospects = self._generate_sample_prospects(campaign, limit)

        logger.info(f"✅ Found {len(sample_prospects)} prospects")

        return sample_prospects


    async def enrich_prospect(self, prospect: Prospect) -> Prospect:
        """
        Enrich prospect with additional data

        Adds:
        - Company information (size, industry, tech stack)
        - Recent news/funding
        - Pain points based on industry
        - Technologies used
        """

        logger.info(f"🔍 Enriching prospect: {prospect.first_name} {prospect.last_name} at {prospect.company_name}")

        if not self.client:
            logger.warning("⚠️  Simulating enrichment (no API key)")
            return self._simulate_enrichment(prospect)

        try:
            # Use Claude to research and enrich
            prompt = f"""You are a B2B research AI. Research this prospect and provide structured enrichment data.

Prospect Information:
- Name: {prospect.first_name} {prospect.last_name}
- Title: {prospect.job_title}
- Company: {prospect.company_name}
- Industry: {prospect.company_industry or 'Unknown'}
- Company Size: {prospect.company_size or 'Unknown'}

Your task:
1. Identify likely pain points for someone in their role/industry
2. Estimate tech stack they might be using
3. Suggest recent business trends/challenges they face
4. Identify what would motivate them to consider AI automation

Return a JSON object with:
{{
  "pain_points": ["list of 3-5 specific pain points"],
  "technologies_used": ["list of likely technologies"],
  "recent_trends": ["list of 2-3 industry trends/challenges"],
  "motivation_factors": ["what would make them interested in AI automation"]
}}"""

            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse Claude's response
            response_text = message.content[0].text

            # Extract JSON from response
            try:
                # Try to find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                enrichment_data = json.loads(json_str)

                # Update prospect with enrichment data
                prospect.pain_points = enrichment_data.get("pain_points", [])
                prospect.technologies_used = enrichment_data.get("technologies_used", [])
                prospect.recent_news = enrichment_data.get("recent_trends", [])
                prospect.custom_fields["motivation_factors"] = enrichment_data.get("motivation_factors", [])

                logger.info(f"✅ Enriched prospect with {len(prospect.pain_points)} pain points")

            except json.JSONDecodeError:
                logger.warning("⚠️  Could not parse enrichment JSON, using simulation")
                return self._simulate_enrichment(prospect)

        except Exception as e:
            logger.error(f"❌ Enrichment failed: {e}")
            return self._simulate_enrichment(prospect)

        prospect.updated_at = datetime.utcnow()
        return prospect


    async def score_prospect(self, prospect: Prospect, campaign: Dict) -> ProspectScore:
        """
        Score prospect for outreach priority

        Scoring factors:
        - Fit score: How well they match ICP
        - Intent score: Likelihood they need solution
        - Timing score: Likelihood they'll buy soon
        - Authority score: Decision-making power
        - Budget score: Estimated budget fit
        """

        logger.info(f"📊 Scoring prospect: {prospect.first_name} {prospect.last_name}")

        if not self.client:
            return self._simulate_scoring(prospect)

        try:
            prompt = f"""You are a B2B sales AI. Score this prospect for outreach priority on a 0-100 scale.

Prospect:
- Name: {prospect.first_name} {prospect.last_name}
- Title: {prospect.job_title}
- Company: {prospect.company_name} ({prospect.company_size})
- Industry: {prospect.company_industry}
- Pain Points: {', '.join(prospect.pain_points)}

Campaign Criteria:
- Target Industries: {campaign.get('target_industries', [])}
- Target Sizes: {campaign.get('target_company_sizes', [])}
- Target Titles: {campaign.get('target_job_titles', [])}
- Value Prop: {campaign.get('value_proposition', '')}

Score on these dimensions (0-100 for each):
1. Fit Score: How well they match ideal customer profile
2. Intent Score: Likelihood they need AI automation solution
3. Timing Score: Likelihood they'll buy in next 3 months
4. Authority Score: Decision-making power (title, seniority)
5. Budget Score: Estimated budget fit (company size, industry)

Return JSON:
{{
  "fit_score": 0-100,
  "intent_score": 0-100,
  "timing_score": 0-100,
  "authority_score": 0-100,
  "budget_score": 0-100,
  "total_score": average of above,
  "reasoning": "2-3 sentences explaining the score and whether to prioritize this prospect"
}}"""

            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse scoring
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                score_data = json.loads(json_str)

                score = ProspectScore(
                    total_score=score_data.get("total_score", 50),
                    fit_score=score_data.get("fit_score", 50),
                    intent_score=score_data.get("intent_score", 50),
                    timing_score=score_data.get("timing_score", 50),
                    authority_score=score_data.get("authority_score", 50),
                    budget_score=score_data.get("budget_score", 50),
                    reasoning=score_data.get("reasoning", "No reasoning provided")
                )

                logger.info(f"✅ Scored {score.total_score}/100 - {score.reasoning[:100]}")

                return score

            except json.JSONDecodeError:
                logger.warning("⚠️  Could not parse scoring JSON, using simulation")
                return self._simulate_scoring(prospect)

        except Exception as e:
            logger.error(f"❌ Scoring failed: {e}")
            return self._simulate_scoring(prospect)


    def _generate_sample_prospects(self, campaign: Dict, limit: int) -> List[Prospect]:
        """Generate sample prospects based on OUTREACH_READY_TO_EXECUTE.md data"""

        sample_prospects_data = [
            {
                "first_name": "Sarah",
                "last_name": "Martinez",
                "email": "smartinez@premiumpe ts.com",
                "job_title": "VP Operations",
                "company_name": "Premium Pets Co",
                "company_size": "50-100",
                "company_industry": "E-Commerce - Pet Products",
                "linkedin_url": "https://linkedin.com/in/sarah-martinez-ops"
            },
            {
                "first_name": "Michael",
                "last_name": "Chen",
                "email": "mchen@luxfashion.com",
                "job_title": "COO",
                "company_name": "Lux Fashion Direct",
                "company_size": "75-150",
                "company_industry": "E-Commerce - Fashion",
                "linkedin_url": "https://linkedin.com/in/michael-chen-coo"
            },
            {
                "first_name": "Jennifer",
                "last_name": "Adams",
                "email": "jadams@marketplacepro.com",
                "job_title": "VP Engineering",
                "company_name": "MarketplacePro",
                "company_size": "100-250",
                "company_industry": "E-Commerce - Marketplace",
                "linkedin_url": "https://linkedin.com/in/jennifer-adams-tech"
            },
            {
                "first_name": "David",
                "last_name": "Thompson",
                "email": "dthompson@boxmonthly.com",
                "job_title": "Director of Operations",
                "company_name": "Box Monthly",
                "company_size": "50-100",
                "company_industry": "E-Commerce - Subscription",
                "linkedin_url": "https://linkedin.com/in/david-thompson-ops"
            },
            {
                "first_name": "Lisa",
                "last_name": "Wong",
                "email": "lwong@printcustom.com",
                "job_title": "COO",
                "company_name": "PrintCustom",
                "company_size": "60-120",
                "company_industry": "E-Commerce - Print on Demand",
                "linkedin_url": "https://linkedin.com/in/lisa-wong-operations"
            },
        ]

        prospects = []
        for data in sample_prospects_data[:limit]:
            prospect = Prospect(
                **data,
                source="research_ai_sample",
                campaign_id=campaign.get("id"),
                created_at=datetime.utcnow()
            )
            prospects.append(prospect)

        return prospects


    def _simulate_enrichment(self, prospect: Prospect) -> Prospect:
        """Simulate enrichment when API not available"""

        # Add sample pain points based on industry
        industry_pain_points = {
            "E-Commerce": [
                "Customer support tickets overwhelming team",
                "Order processing taking too long",
                "Can't scale support during peak seasons",
                "Returns processing manual and time-consuming"
            ],
            "SaaS": [
                "Customer onboarding taking too long",
                "Support tickets piling up",
                "Churn due to slow time-to-value",
                "Integration requests backlog"
            ]
        }

        industry_key = next((k for k in industry_pain_points.keys() if k in (prospect.company_industry or "")), "E-Commerce")
        prospect.pain_points = industry_pain_points[industry_key][:3]

        prospect.technologies_used = ["Shopify", "Zendesk", "Klaviyo", "Google Analytics"]
        prospect.recent_news = ["Scaling operations", "Increasing customer demand"]

        return prospect


    def _simulate_scoring(self, prospect: Prospect) -> ProspectScore:
        """Simulate scoring when API not available"""

        # Simple heuristic scoring
        fit_score = 75.0
        intent_score = 70.0
        timing_score = 65.0

        # Higher authority for VP/C-level
        authority_score = 90.0 if any(title in prospect.job_title for title in ["VP", "COO", "CEO", "CTO"]) else 60.0

        # Higher budget for larger companies
        budget_score = 80.0 if "100" in (prospect.company_size or "") else 70.0

        total = (fit_score + intent_score + timing_score + authority_score + budget_score) / 5

        return ProspectScore(
            total_score=total,
            fit_score=fit_score,
            intent_score=intent_score,
            timing_score=timing_score,
            authority_score=authority_score,
            budget_score=budget_score,
            reasoning=f"Good fit: {prospect.job_title} at {prospect.company_name}. Authority level high. Company size appropriate for AI automation investment."
        )


# Global instance
_research_ai = None


def get_research_ai() -> ResearchAI:
    """Get or create global Research AI instance"""
    global _research_ai
    if _research_ai is None:
        _research_ai = ResearchAI()
    return _research_ai
