#!/usr/bin/env python3
"""
AI Marketing Engine - Demo Script

Demonstrates the complete autonomous marketing automation workflow:
1. Research AI finds and scores prospects
2. Human approves prospects (simulated)
3. Outreach AI personalizes and sends emails
4. Conversation AI handles replies
5. Orchestrator coordinates everything

Run this to see the system in action!
"""

import asyncio
import sys
from datetime import datetime

from marketing_engine.models.prospect import Campaign
from marketing_engine.agents.orchestrator import get_orchestrator


async def run_demo():
    """Run complete marketing engine demo"""

    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              🚀 AI MARKETING ENGINE - DEMO                   ║
║                                                               ║
║  Autonomous Revenue Generation System                        ║
║  Finds → Qualifies → Contacts → Converts                     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")

    # Initialize orchestrator
    orchestrator = get_orchestrator()

    # Create demo campaign
    print("\n📋 Step 1: Creating Campaign...")
    campaign = Campaign(
        id="demo_campaign_1",
        name="E-Commerce AI Automation Outreach",
        description="Target e-commerce companies for customer support automation",
        target_industries=["E-Commerce", "Retail", "D2C"],
        target_company_sizes=["50-100", "100-250"],
        target_job_titles=["VP Operations", "COO", "Director of Operations"],
        target_seniority=["VP", "C-Level", "Director"],
        value_proposition="Reduce customer support costs by 70% through AI automation",
        pain_points_addressed=[
            "Overwhelmed support teams",
            "Scaling challenges",
            "High support costs",
            "Slow response times"
        ],
        daily_outreach_limit=50,
        active=True
    )

    orchestrator.campaigns[campaign.id] = campaign
    print(f"✅ Campaign created: {campaign.name}")
    print(f"   Target: {', '.join(campaign.target_industries)}")
    print(f"   Daily limit: {campaign.daily_outreach_limit} emails")

    # Step 2: Morning Research (6-8 AM)
    print("\n\n🔍 Step 2: Morning Research (6:00-8:00 AM)")
    print("━" * 60)
    print("Research AI finding and scoring prospects...")

    prospects = await orchestrator.morning_research(campaign)

    print(f"\n✅ Research complete - Found {len(prospects)} prospects")
    print("\nTop 5 Prospects:")
    print("━" * 60)

    for i, p in enumerate(prospects[:5], 1):
        score = p.score.total_score if p.score else 0
        print(f"{i}. {p.first_name} {p.last_name}")
        print(f"   {p.job_title} at {p.company_name}")
        print(f"   Score: {score}/100 ({p.score.reasoning[:60] if p.score else ''}...)")
        if p.pain_points:
            print(f"   Pain Point: {p.pain_points[0]}")
        print()

    # Step 3: Prepare approval queue
    print("\n📋 Step 3: Preparing Approval Queue (8:00-9:00 AM)")
    print("━" * 60)

    await orchestrator.morning_approval_prep(campaign)

    print(f"✅ Approval queue ready: {len(orchestrator.pending_approvals)} prospects")
    print("\n⏰ [9:00 AM] Waiting for human approval...")
    print("   (In production, Campaign Manager reviews and approves in 15 minutes)")

    # Simulate human approval
    await asyncio.sleep(1)
    prospect_ids = [p.id for p in orchestrator.pending_approvals[:10]]  # Approve top 10

    print(f"\n👤 Human approving {len(prospect_ids)} top prospects...")
    approved = await orchestrator.approve_prospects(prospect_ids, approved_by="demo_user")

    print(f"✅ {approved} prospects approved for outreach")

    # Step 4: Morning outreach batch
    print("\n\n📧 Step 4: Morning Outreach Batch (10:00-11:00 AM)")
    print("━" * 60)
    print("Outreach AI personalizing and sending emails...\n")

    # Use dry run so we don't actually send emails in demo
    print("ℹ️  Running in DRY RUN mode (no actual emails sent)\n")

    # Get first 3 approved prospects for demo
    approved_prospects = [
        p for p in orchestrator.prospects.values()
        if p.approved_for_outreach and p.status.value == "qualified"
    ][:3]

    # Create default template
    template = orchestrator._create_default_template()
    orchestrator.templates[template.id] = template

    # Show personalization for each
    from marketing_engine.agents.outreach_ai import get_outreach_ai
    outreach_ai = get_outreach_ai()

    for i, prospect in enumerate(approved_prospects, 1):
        print(f"\n[Email {i}/3] Personalizing for {prospect.first_name} {prospect.last_name}...")

        personalized = await outreach_ai.personalize_email(
            prospect,
            template,
            campaign.__dict__
        )

        print(f"\n   To: {prospect.email}")
        print(f"   Subject: {personalized['subject']}")
        print(f"   Preview:\n")

        # Show first 200 chars of body
        body_preview = personalized['body'][:200].replace('\n', '\n   ')
        print(f"   {body_preview}...")
        print()

    print("✅ Morning batch complete - 3 emails personalized (dry run)")

    # Step 5: Reply handling simulation
    print("\n\n📨 Step 5: Reply Handling (12:00-2:00 PM)")
    print("━" * 60)

    # Simulate a reply from first prospect
    if approved_prospects:
        prospect = approved_prospects[0]

        # Simulate a positive reply
        simulated_reply = {
            "subject": f"Re: {template.subject}",
            "body": "Hi James, this sounds interesting. I'd like to learn more about how you can help us reduce support costs. Do you have time for a quick call this week?",
            "timestamp": datetime.utcnow().isoformat()
        }

        print(f"\n✉️  New reply received from {prospect.first_name} {prospect.last_name}")
        print(f"   \"{simulated_reply['body'][:80]}...\"")

        from marketing_engine.agents.conversation_ai import get_conversation_ai
        conversation_ai = get_conversation_ai()

        print("\n🤖 Conversation AI analyzing reply...")

        result = await conversation_ai.handle_reply(
            prospect=prospect,
            reply_email=simulated_reply,
            campaign=campaign.__dict__,
            auto_respond=True  # Auto-respond for demo
        )

        analysis = result.get('analysis', {})
        draft = result.get('draft_reply', {})

        print(f"\n✅ Analysis complete:")
        print(f"   Intent: {analysis.get('intent', 'unknown')}")
        print(f"   Sentiment: {analysis.get('sentiment', 'unknown')}")
        print(f"   Qualification Score: {analysis.get('qualification', {}).get('total_score', 0)}/100")
        print(f"   Action: {result.get('action', 'unknown')}")

        if draft:
            print(f"\n📧 Drafted response:")
            print(f"   Subject: {draft.get('subject', '')}")
            print(f"   Body:\n")
            body_lines = draft.get('body', '').split('\n')
            for line in body_lines[:5]:  # Show first 5 lines
                print(f"   {line}")
            if len(body_lines) > 5:
                print("   ...")

        if result.get('auto_sent'):
            print(f"\n✅ Response auto-sent (dry run)")
        elif result.get('action') == 'escalated_to_human':
            print(f"\n🚨 Escalated to human for review")

    # Step 6: Daily summary
    print("\n\n📊 Step 6: Daily Summary Report (5:00 PM)")
    print("━" * 60)

    summary = await orchestrator.evening_summary(campaign)

    print(f"\n{'═' * 60}")
    print("THAT'S IT! The AI Marketing Engine:")
    print("• Found and scored prospects automatically")
    print("• Prepared approval queue for human (15 min)")
    print("• Personalized and sent outreach emails")
    print("• Handled replies intelligently")
    print("• Generated summary report")
    print(f"{'═' * 60}\n")

    print("\n🎯 Next Steps:")
    print("1. Set up API keys (ANTHROPIC_API_KEY, SENDGRID_API_KEY)")
    print("2. Configure campaign targets")
    print("3. Create email templates")
    print("4. Schedule daily workflow (cron job)")
    print("5. Review approvals each morning (15 min)")
    print("6. Close deals! 💰")

    print("\n\n📚 Documentation:")
    print("- Full spec: AI_MARKETING_ENGINE_SPEC.md")
    print("- Outreach guide: OUTREACH_READY_TO_EXECUTE.md")
    print("- API docs: http://localhost:8700/docs (when server running)")

    print("\n\n✅ Demo complete!\n")


if __name__ == "__main__":
    print("Starting AI Marketing Engine Demo...")
    print("(This may take a minute...)\n")

    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
