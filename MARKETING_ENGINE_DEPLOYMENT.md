# AI Marketing Engine - Deployment Guide

## Overview

This is the complete deployment guide for the **AI Marketing Engine** - an autonomous revenue generation system that finds prospects, personalizes outreach, handles conversations, and books meetings with minimal human oversight.

**What it does:**
- Finds 20-50 prospects daily matching your ICP
- Scores and qualifies each prospect automatically
- Sends 50 personalized emails per day
- Handles replies intelligently
- Books discovery calls autonomously
- Generates daily performance reports

**Human time required: ~1 hour/day**
- 15 min morning: Approve prospect list
- 15 min afternoon: Review high-value replies
- 2-4 hours: Conduct sales calls and close deals

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AI                          │
│              (Coordinates entire workflow)                  │
└──────────┬──────────────────────────────────────┬──────────┘
           │                                       │
    ┌──────▼──────┐    ┌──────────────┐    ┌─────▼──────┐
    │ Research AI │    │ Outreach AI  │    │Conversation│
    │             │    │              │    │    AI      │
    │• Find       │    │• Personalize │    │• Analyze   │
    │• Enrich     │    │• Send        │    │• Qualify   │
    │• Score      │    │• A/B Test    │    │• Respond   │
    └─────────────┘    └──────────────┘    └────────────┘
           │                    │                    │
           └────────────────────┴────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Human Interface   │
                    │  (FastAPI + Web)   │
                    └────────────────────┘
```

---

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Anthropic API key (Claude)
- SendGrid API key (email sending)
- Optional: LinkedIn Sales Navigator, Apollo.io, Hunter.io

### 2. Installation

```bash
cd /Users/jamessunheart/Development/SERVICES/ai-automation

# Install dependencies
pip install fastapi uvicorn anthropic sendgrid pydantic

# Or use requirements.txt if available
pip install -r requirements.txt
```

### 3. Environment Setup

Create `.env` file or export environment variables:

```bash
# Required
export ANTHROPIC_API_KEY="your-claude-api-key"
export SENDGRID_API_KEY="your-sendgrid-key"
export SENDGRID_FROM_EMAIL="james@fullpotential.com"
export SENDGRID_FROM_NAME="James from Full Potential AI"

# Optional
export SENDGRID_DAILY_LIMIT="500"
```

### 4. Run Demo

Test the system first with the demo:

```bash
python3 demo_marketing_engine.py
```

This will simulate the entire workflow without sending real emails.

### 5. Start API Server

```bash
python3 main.py
```

Or with uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8700 --reload
```

Access:
- Landing page: http://localhost:8700
- API docs: http://localhost:8700/docs
- Marketing API: http://localhost:8700/api/marketing/

---

## Configuration

### Create Campaign

```python
from marketing_engine.models.prospect import Campaign

campaign = Campaign(
    name="E-Commerce AI Automation Outreach",
    description="Target e-commerce for support automation",
    target_industries=["E-Commerce", "SaaS", "Retail"],
    target_company_sizes=["50-100", "100-250"],
    target_job_titles=["VP Operations", "COO", "CTO"],
    value_proposition="Reduce costs by 70% through AI automation",
    pain_points_addressed=[
        "High support costs",
        "Scaling challenges",
        "Slow response times"
    ],
    daily_outreach_limit=50,
    active=True
)
```

### Create Email Templates

```python
from marketing_engine.models.prospect import EmailTemplate

template = EmailTemplate(
    name="Initial Outreach - E-Commerce",
    subject="Cut {{company_name}}'s support costs by 70%",
    body="""Hi {{first_name}},

I noticed {{company_name}} has been scaling in {{industry}}. Quick question: Are you spending $50k-$100k/year on customer support for repetitive tasks?

We help companies like yours reduce support costs by 70% through AI automation.

**Real numbers:**
- Traditional: 3 reps @ $60k = $180k/year
- AI automation: $84k/year for 24/7 coverage
- **Net savings: $96k/year**

Would a 15-minute call this week make sense?""",
    sequence_position=1,
    template_type="initial"
)
```

---

## Daily Workflow Schedule

Set up cron jobs to automate the daily workflow:

### Option 1: Cron Jobs (Recommended)

```bash
# Edit crontab
crontab -e

# Add these entries:
# 6 AM - Morning research
0 6 * * * cd /Users/jamessunheart/Development/SERVICES/ai-automation && python3 -c "import asyncio; from marketing_engine.agents.orchestrator import get_orchestrator; asyncio.run(get_orchestrator().morning_research('campaign_id'))"

# 10 AM - Morning outreach
0 10 * * * cd /Users/jamessunheart/Development/SERVICES/ai-automation && python3 -c "import asyncio; from marketing_engine.agents.orchestrator import get_orchestrator; asyncio.run(get_orchestrator().morning_outreach_batch('campaign_id'))"

# 12 PM - Check replies
0 12 * * * cd /Users/jamessunheart/Development/SERVICES/ai-automation && python3 -c "import asyncio; from marketing_engine.agents.orchestrator import get_orchestrator; asyncio.run(get_orchestrator().check_and_process_replies('campaign_id'))"

# 2 PM - Afternoon outreach
0 14 * * * cd /Users/jamessunheart/Development/SERVICES/ai-automation && python3 -c "import asyncio; from marketing_engine.agents.orchestrator import get_orchestrator; asyncio.run(get_orchestrator().afternoon_outreach_batch('campaign_id'))"

# 5 PM - Daily summary
0 17 * * * cd /Users/jamessunheart/Development/SERVICES/ai-automation && python3 -c "import asyncio; from marketing_engine.agents.orchestrator import get_orchestrator; asyncio.run(get_orchestrator().evening_summary('campaign_id'))"
```

### Option 2: Custom Scheduler Script

Create `run_daily_workflow.py`:

```python
#!/usr/bin/env python3
import asyncio
import sys
from marketing_engine.agents.orchestrator import get_orchestrator

async def main():
    campaign_id = sys.argv[1] if len(sys.argv) > 1 else "campaign_1"
    orchestrator = get_orchestrator()
    await orchestrator.run_daily_workflow(campaign_id)

if __name__ == "__main__":
    asyncio.run(main())
```

Then schedule it:
```bash
0 6 * * * cd /path/to/ai-automation && python3 run_daily_workflow.py campaign_1
```

---

## API Endpoints

### Campaigns

```bash
# Create campaign
POST /api/marketing/campaigns
{
  "name": "Campaign Name",
  "target_industries": ["E-Commerce"],
  ...
}

# List campaigns
GET /api/marketing/campaigns

# Run daily workflow
POST /api/marketing/campaigns/{campaign_id}/run-workflow
```

### Prospects

```bash
# Get prospects for campaign
GET /api/marketing/campaigns/{campaign_id}/prospects?status=qualified

# Get pending approvals
GET /api/marketing/prospects/pending-approval

# Approve prospects (Human touchpoint)
POST /api/marketing/prospects/approve
{
  "prospect_ids": ["prospect_1", "prospect_2"],
  "approved_by": "james"
}
```

### Outreach

```bash
# Personalize email
POST /api/marketing/outreach/personalize
{
  "prospect_id": "prospect_1",
  "template_id": "template_1",
  "campaign_id": "campaign_1"
}

# Send email
POST /api/marketing/outreach/send
{
  "prospect_id": "prospect_1",
  "subject": "...",
  "body": "...",
  "campaign_id": "campaign_1",
  "dry_run": false
}
```

### Analytics

```bash
# Get dashboard
GET /api/marketing/analytics/dashboard?campaign_id=campaign_1

# Get daily summary
GET /api/marketing/daily-summary/{campaign_id}
```

---

## Human Workflow

### Morning (9:00 AM - 15 minutes)

1. Check email for "Approval Queue Ready" notification
2. Visit: `http://localhost:8700/api/marketing/prospects/pending-approval`
3. Review top scored prospects (sorted by score)
4. Approve 20-50 prospects for outreach
5. System automatically sends emails at 10 AM

### Afternoon (12:00 PM - 15 minutes)

1. Check "High-Value Replies" notification
2. Visit: `http://localhost:8700/api/marketing/replies/pending`
3. Review AI-drafted responses
4. Approve or modify responses
5. System sends approved responses

### Throughout Day (2-4 hours)

1. Conduct discovery calls with qualified prospects
2. Send proposals
3. Close deals
4. Update CRM manually or via API

---

## Integration with External Services

### LinkedIn Sales Navigator

For production prospect finding:

```python
# In research_ai.py, replace find_prospects() with:

async def find_prospects_from_linkedin(self, campaign, limit=20):
    # Use Phantombuster or LinkedIn API
    # to scrape Sales Navigator results
    pass
```

### Hunter.io for Email Finding

```python
# In research_ai.py

import requests

async def find_email(self, first_name, last_name, company_domain):
    response = requests.get(
        f"https://api.hunter.io/v2/email-finder",
        params={
            "domain": company_domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": os.getenv('HUNTER_API_KEY')
        }
    )
    return response.json()
```

### HubSpot/Salesforce CRM

```python
# Create services/crm_service.py

class CRMService:
    def sync_prospect(self, prospect):
        # Sync to HubSpot/Salesforce
        pass

    def update_deal_stage(self, prospect_id, stage):
        # Update pipeline stage
        pass
```

---

## Monitoring & Logging

### Daily Email Reports

Configure to send summary to your email:

```python
# In orchestrator.py, add to evening_summary():

from services.email_service import get_email_service

email_service = get_email_service()
email_service.send_email(
    to_email="james@fullpotential.com",
    to_name="James",
    subject=f"Daily Marketing Report - {date}",
    body_html=generate_report_html(summary)
)
```

### Error Alerts

Use logging to track errors:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('marketing_engine.log'),
        logging.StreamHandler()
    ]
)
```

---

## Production Deployment

### 1. Deploy to Server

```bash
# Copy to production server
scp -r /Users/jamessunheart/Development/SERVICES/ai-automation root@your-server:/opt/fpai/

# SSH to server
ssh root@your-server

# Install dependencies
cd /opt/fpai/ai-automation
pip3 install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="..."
export SENDGRID_API_KEY="..."
```

### 2. Run with Systemd

Create `/etc/systemd/system/ai-marketing.service`:

```ini
[Unit]
Description=AI Marketing Engine API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fpai/ai-automation
Environment="ANTHROPIC_API_KEY=your-key"
Environment="SENDGRID_API_KEY=your-key"
ExecStart=/usr/bin/python3 /opt/fpai/ai-automation/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl enable ai-marketing
systemctl start ai-marketing
systemctl status ai-marketing
```

### 3. Nginx Reverse Proxy

Add to nginx config:

```nginx
location /api/marketing {
    proxy_pass http://localhost:8700/api/marketing;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## Cost Structure

### AI/Automation Costs

- **Claude API**: ~$50-100/month (for 50 prospects/day)
- **SendGrid**: $15/month (Essentials plan, 50k emails)
- **Hunter.io**: $49/month (Starter plan, email finding)
- **Phantombuster**: $30/month (LinkedIn automation)

**Total**: ~$150-200/month

### Human Costs

- **Campaign Manager**: $500/month (1 hour/day @ $25/hr)
- **Sales Closer**: $2,000/month (20 hours/week @ $25/hr)

**Total**: ~$2,500/month

### Total Operating Cost

**$2,650-2,700/month** for autonomous marketing that can generate $20-30k MRR

**Profit margin: 85-90%**

---

## Scaling

### Increase Daily Volume

To go from 50 → 100 emails/day:

1. Increase `daily_outreach_limit` in campaign
2. Upgrade SendGrid plan if needed
3. Add another human approver (split morning approvals)

### Multiple Campaigns

Run campaigns in parallel for different ICPs:

```python
campaign_ecommerce = Campaign(name="E-Commerce", ...)
campaign_saas = Campaign(name="SaaS", ...)
campaign_healthcare = Campaign(name="Healthcare", ...)

# Run all in parallel
await asyncio.gather(
    orchestrator.run_daily_workflow(campaign_ecommerce.id),
    orchestrator.run_daily_workflow(campaign_saas.id),
    orchestrator.run_daily_workflow(campaign_healthcare.id)
)
```

---

## Troubleshooting

### Emails not sending

```bash
# Check SendGrid API key
python3 -c "from marketing_engine.services.email_service import get_email_service; print(get_email_service().api_key)"

# Test email
python3 -c "from marketing_engine.services.email_service import get_email_service; print(get_email_service().send_email('test@example.com', 'Test', 'Test Subject', '<p>Test</p>'))"
```

### Claude API errors

```bash
# Check API key
python3 -c "from marketing_engine.agents.research_ai import get_research_ai; print(get_research_ai().client)"

# Test API call
python3 -c "import anthropic; client = anthropic.Anthropic(); print(client.messages.create(model='claude-sonnet-4-5-20250929', max_tokens=100, messages=[{'role': 'user', 'content': 'test'}]))"
```

### View logs

```bash
tail -f marketing_engine.log
```

---

## Next Steps

1. **Week 1**: Set up infrastructure, test with demo
2. **Week 2**: Create first campaign, run dry-run outreach
3. **Week 3**: Go live with 10 emails/day, validate personalization
4. **Week 4**: Scale to 50 emails/day, optimize based on metrics
5. **Month 2**: Add second campaign, scale to 100 emails/day
6. **Month 3**: Full automation at scale, generating $20-30k MRR

---

## Support & Resources

- **Full Spec**: `AI_MARKETING_ENGINE_SPEC.md`
- **Outreach Guide**: `OUTREACH_READY_TO_EXECUTE.md`
- **API Docs**: http://localhost:8700/docs
- **Demo**: `python3 demo_marketing_engine.py`

---

**Built with:**
- FastAPI (Web framework)
- Claude Sonnet 4.5 (AI intelligence)
- SendGrid (Email delivery)
- Pydantic (Data models)

**Version**: 1.0.0
**License**: Proprietary
**Author**: Full Potential AI
