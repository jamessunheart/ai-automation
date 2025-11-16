"""Marketing metrics integration for daily reports"""

import requests
import json
from datetime import datetime
from pathlib import Path


def get_marketing_metrics() -> dict:
    """Fetch marketing metrics from the dashboard API"""
    try:
        # Try production first
        response = requests.get("http://198.54.123.234:8700/api/marketing/dashboard/daily-report", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass

    # Fallback to localhost
    try:
        response = requests.get("http://localhost:8700/api/marketing/dashboard/daily-report", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass

    # Return empty metrics if service unavailable
    return {
        "date": datetime.now().date().isoformat(),
        "summary": {
            "total_campaigns": 0,
            "active_campaigns": 0,
            "emails_sent_today": 0,
            "leads_generated_today": 0,
            "meetings_booked_today": 0
        },
        "email_performance": {
            "sent": 0,
            "delivered": 0,
            "opened": 0,
            "clicked": 0,
            "replied": 0,
            "open_rate": 0,
            "click_rate": 0,
            "reply_rate": 0
        },
        "ai_agents": {
            "research": {
                "prospects_analyzed": 0,
                "icp_matches": 0
            },
            "outreach": {
                "emails_sent": 0,
                "open_rate": "0.0%"
            },
            "conversation": {
                "active_conversations": 0,
                "qualified_leads": 0
            }
        },
        "revenue_metrics": {
            "pipeline_value": 0,
            "closed_deals": 0,
            "revenue_generated": 0
        }
    }


def format_marketing_section(metrics: dict) -> str:
    """Format marketing metrics for daily report"""
    summary = metrics.get("summary", {})
    email = metrics.get("email_performance", {})
    agents = metrics.get("ai_agents", {})
    revenue = metrics.get("revenue_metrics", {})

    report = f"""
## 🚀 AI Marketing Engine

### Campaign Summary
- **Total Campaigns**: {summary.get('total_campaigns', 0)}
- **Active Campaigns**: {summary.get('active_campaigns', 0)}
- **Emails Sent Today**: {summary.get('emails_sent_today', 0)}
- **Leads Generated Today**: {summary.get('leads_generated_today', 0)}
- **Meetings Booked Today**: {summary.get('meetings_booked_today', 0)}

### Email Performance (All-Time)
- **Total Sent**: {email.get('sent', 0):,}
- **Delivered**: {email.get('delivered', 0):,}
- **Opened**: {email.get('opened', 0):,} ({email.get('open_rate', 0):.1f}%)
- **Clicked**: {email.get('clicked', 0):,} ({email.get('click_rate', 0):.1f}%)
- **Replied**: {email.get('replied', 0):,} ({email.get('reply_rate', 0):.1f}%)

### AI Agents Activity
**Research AI**
- Prospects Analyzed: {agents.get('research', {}).get('prospects_analyzed', 0):,}
- ICP Matches: {agents.get('research', {}).get('icp_matches', 0):,}

**Outreach AI**
- Emails Sent: {agents.get('outreach', {}).get('emails_sent', 0):,}
- Open Rate: {agents.get('outreach', {}).get('open_rate', 'N/A')}

**Conversation AI**
- Active Conversations: {agents.get('conversation', {}).get('active_conversations', 0)}
- Qualified Leads: {agents.get('conversation', {}).get('qualified_leads', 0)}

### Revenue Impact
- **Pipeline Value**: ${revenue.get('pipeline_value', 0):,}
- **Closed Deals**: {revenue.get('closed_deals', 0)}
- **Revenue Generated**: ${revenue.get('revenue_generated', 0):,}

---
"""

    return report


def generate_daily_report() -> str:
    """Generate complete daily report with marketing metrics"""
    metrics = get_marketing_metrics()
    report = format_marketing_section(metrics)

    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"# Daily Report - {metrics.get('date', 'Unknown Date')}\n"
    header += f"Generated: {timestamp}\n\n"

    return header + report


def save_daily_report(filename: str = None):
    """Generate and save daily report to file"""
    if filename is None:
        filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.md"

    report = generate_daily_report()

    # Save to reports directory
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    filepath = reports_dir / filename
    with open(filepath, 'w') as f:
        f.write(report)

    print(f"Daily report saved to: {filepath}")
    return str(filepath)


if __name__ == "__main__":
    # Generate and print report
    report = generate_daily_report()
    print(report)

    # Save to file
    save_daily_report()
