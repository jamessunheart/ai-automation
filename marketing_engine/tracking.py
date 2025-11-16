"""Campaign tracking and event logging for marketing analytics"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum


class EventType(str, Enum):
    """Marketing event types"""
    CAMPAIGN_CREATED = "campaign_created"
    CAMPAIGN_STARTED = "campaign_started"
    CAMPAIGN_PAUSED = "campaign_paused"
    CAMPAIGN_COMPLETED = "campaign_completed"
    EMAIL_SENT = "email_sent"
    EMAIL_DELIVERED = "email_delivered"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    EMAIL_REPLIED = "email_replied"
    EMAIL_BOUNCED = "email_bounced"
    PROSPECT_ANALYZED = "prospect_analyzed"
    PROSPECT_CONTACTED = "prospect_contacted"
    LEAD_QUALIFIED = "lead_qualified"
    MEETING_BOOKED = "meeting_booked"
    DEAL_CREATED = "deal_created"
    DEAL_WON = "deal_won"
    DEAL_LOST = "deal_lost"


class CampaignTracker:
    """Track campaign events and metrics"""

    def __init__(self):
        self.data_dir = Path("marketing_data")
        self.data_dir.mkdir(exist_ok=True)
        self.campaigns_file = self.data_dir / "campaigns.json"
        self.events_file = self.data_dir / "events.json"
        self._ensure_files()

    def _ensure_files(self):
        """Ensure data files exist"""
        if not self.campaigns_file.exists():
            with open(self.campaigns_file, 'w') as f:
                json.dump([], f)
        if not self.events_file.exists():
            with open(self.events_file, 'w') as f:
                json.dump([], f)

    def create_campaign(self, campaign_data: Dict) -> str:
        """Create a new campaign and return campaign ID"""
        campaigns = self._load_campaigns()

        campaign_id = f"campaign_{datetime.utcnow().timestamp()}"
        campaign = {
            "id": campaign_id,
            "name": campaign_data.get("name"),
            "icp": campaign_data.get("icp"),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            # Metrics
            "emails_sent": 0,
            "emails_delivered": 0,
            "emails_opened": 0,
            "emails_clicked": 0,
            "emails_replied": 0,
            "emails_bounced": 0,
            "prospects_analyzed": 0,
            "companies_researched": 0,
            "icp_matches": 0,
            "conversations_active": 0,
            "leads_qualified": 0,
            "meetings_booked": 0,
            "deals_created": 0,
            "closed_deals": 0,
            "pipeline_value": 0,
            "revenue_generated": 0
        }

        campaigns.append(campaign)
        self._save_campaigns(campaigns)

        # Log event
        self.log_event(EventType.CAMPAIGN_CREATED, campaign_id, {
            "campaign_name": campaign_data.get("name")
        })

        return campaign_id

    def update_campaign_metric(self, campaign_id: str, metric: str, increment: int = 1):
        """Update a campaign metric"""
        campaigns = self._load_campaigns()

        for campaign in campaigns:
            if campaign["id"] == campaign_id:
                if metric in campaign:
                    campaign[metric] += increment
                    campaign["updated_at"] = datetime.utcnow().isoformat()
                    self._save_campaigns(campaigns)
                    return True
        return False

    def get_campaign(self, campaign_id: str) -> Optional[Dict]:
        """Get campaign by ID"""
        campaigns = self._load_campaigns()
        for campaign in campaigns:
            if campaign["id"] == campaign_id:
                return campaign
        return None

    def get_all_campaigns(self) -> List[Dict]:
        """Get all campaigns"""
        return self._load_campaigns()

    def log_event(self, event_type: EventType, campaign_id: str, data: Dict = None):
        """Log a marketing event"""
        events = self._load_events()

        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "campaign_id": campaign_id,
            "data": data or {}
        }

        events.append(event)
        self._save_events(events)

        # Update campaign metrics based on event
        self._update_metrics_from_event(event_type, campaign_id, data)

    def _update_metrics_from_event(self, event_type: EventType, campaign_id: str, data: Dict):
        """Automatically update campaign metrics from events"""
        metric_map = {
            EventType.EMAIL_SENT: "emails_sent",
            EventType.EMAIL_DELIVERED: "emails_delivered",
            EventType.EMAIL_OPENED: "emails_opened",
            EventType.EMAIL_CLICKED: "emails_clicked",
            EventType.EMAIL_REPLIED: "emails_replied",
            EventType.EMAIL_BOUNCED: "emails_bounced",
            EventType.PROSPECT_ANALYZED: "prospects_analyzed",
            EventType.LEAD_QUALIFIED: "leads_qualified",
            EventType.MEETING_BOOKED: "meetings_booked",
            EventType.DEAL_CREATED: "deals_created",
            EventType.DEAL_WON: "closed_deals"
        }

        metric = metric_map.get(event_type)
        if metric:
            self.update_campaign_metric(campaign_id, metric, 1)

        # Update revenue metrics
        if event_type == EventType.DEAL_WON and data:
            campaigns = self._load_campaigns()
            for campaign in campaigns:
                if campaign["id"] == campaign_id:
                    campaign["revenue_generated"] += data.get("deal_value", 0)
                    campaign["updated_at"] = datetime.utcnow().isoformat()
                    self._save_campaigns(campaigns)
                    break

    def get_events(self, campaign_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get recent events, optionally filtered by campaign"""
        events = self._load_events()

        if campaign_id:
            events = [e for e in events if e.get("campaign_id") == campaign_id]

        # Sort by timestamp desc and limit
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events[:limit]

    def _load_campaigns(self) -> List[Dict]:
        """Load campaigns from file"""
        try:
            with open(self.campaigns_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def _save_campaigns(self, campaigns: List[Dict]):
        """Save campaigns to file"""
        with open(self.campaigns_file, 'w') as f:
            json.dump(campaigns, f, indent=2)

    def _load_events(self) -> List[Dict]:
        """Load events from file"""
        try:
            with open(self.events_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def _save_events(self, events: List[Dict]):
        """Save events to file"""
        # Keep only last 10,000 events to prevent file from growing indefinitely
        if len(events) > 10000:
            events = events[-10000:]

        with open(self.events_file, 'w') as f:
            json.dump(events, f, indent=2)


# Global tracker instance
tracker = CampaignTracker()
