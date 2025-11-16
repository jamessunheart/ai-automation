"""Marketing Dashboard - Real-time analytics and campaign tracking"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

router = APIRouter()


class MarketingDashboard:
    """Marketing dashboard with real-time metrics and campaign analytics"""

    def __init__(self):
        self.data_dir = Path("marketing_data")
        self.data_dir.mkdir(exist_ok=True)
        self.campaigns_file = self.data_dir / "campaigns.json"
        self.metrics_file = self.data_dir / "metrics.json"

    def get_campaign_metrics(self, campaign_id: Optional[str] = None) -> Dict:
        """Get metrics for all campaigns or specific campaign"""
        try:
            if not self.campaigns_file.exists():
                return self._empty_metrics()

            with open(self.campaigns_file, 'r') as f:
                campaigns = json.load(f)

            if campaign_id:
                campaign = next((c for c in campaigns if c.get('id') == campaign_id), None)
                if not campaign:
                    return self._empty_metrics()
                return self._calculate_campaign_metrics(campaign)

            # Aggregate metrics across all campaigns
            return self._aggregate_metrics(campaigns)
        except Exception as e:
            return self._empty_metrics()

    def get_channel_performance(self) -> Dict:
        """Get performance metrics by channel (Email, Social, etc.)"""
        metrics = self.get_campaign_metrics()

        return {
            "email": {
                "sent": metrics.get("emails_sent", 0),
                "delivered": metrics.get("emails_delivered", 0),
                "opened": metrics.get("emails_opened", 0),
                "clicked": metrics.get("emails_clicked", 0),
                "replied": metrics.get("emails_replied", 0),
                "open_rate": metrics.get("open_rate", 0),
                "click_rate": metrics.get("click_rate", 0),
                "reply_rate": metrics.get("reply_rate", 0)
            },
            "ai_research": {
                "prospects_analyzed": metrics.get("prospects_analyzed", 0),
                "companies_researched": metrics.get("companies_researched", 0),
                "icp_matches": metrics.get("icp_matches", 0)
            },
            "ai_conversation": {
                "conversations_active": metrics.get("conversations_active", 0),
                "leads_qualified": metrics.get("leads_qualified", 0),
                "meetings_booked": metrics.get("meetings_booked", 0)
            }
        }

    def get_daily_report_data(self) -> Dict:
        """Get marketing data formatted for daily report"""
        metrics = self.get_campaign_metrics()
        channels = self.get_channel_performance()

        # Calculate today's activity
        today = datetime.now().date()
        today_metrics = self._get_date_metrics(today)

        return {
            "date": today.isoformat(),
            "summary": {
                "total_campaigns": metrics.get("total_campaigns", 0),
                "active_campaigns": metrics.get("active_campaigns", 0),
                "emails_sent_today": today_metrics.get("emails_sent", 0),
                "leads_generated_today": today_metrics.get("leads_generated", 0),
                "meetings_booked_today": today_metrics.get("meetings_booked", 0)
            },
            "email_performance": channels["email"],
            "ai_agents": {
                "research": {
                    "prospects_analyzed": channels["ai_research"]["prospects_analyzed"],
                    "icp_matches": channels["ai_research"]["icp_matches"]
                },
                "outreach": {
                    "emails_sent": channels["email"]["sent"],
                    "open_rate": f"{channels['email']['open_rate']:.1f}%"
                },
                "conversation": {
                    "active_conversations": channels["ai_conversation"]["conversations_active"],
                    "qualified_leads": channels["ai_conversation"]["leads_qualified"]
                }
            },
            "revenue_metrics": {
                "pipeline_value": metrics.get("pipeline_value", 0),
                "closed_deals": metrics.get("closed_deals", 0),
                "revenue_generated": metrics.get("revenue_generated", 0)
            }
        }

    def _calculate_campaign_metrics(self, campaign: Dict) -> Dict:
        """Calculate metrics for a single campaign"""
        emails_sent = campaign.get("emails_sent", 0)
        emails_delivered = campaign.get("emails_delivered", 0)
        emails_opened = campaign.get("emails_opened", 0)
        emails_clicked = campaign.get("emails_clicked", 0)
        emails_replied = campaign.get("emails_replied", 0)

        return {
            "campaign_id": campaign.get("id"),
            "campaign_name": campaign.get("name"),
            "status": campaign.get("status", "unknown"),
            "emails_sent": emails_sent,
            "emails_delivered": emails_delivered,
            "emails_opened": emails_opened,
            "emails_clicked": emails_clicked,
            "emails_replied": emails_replied,
            "open_rate": (emails_opened / emails_delivered * 100) if emails_delivered > 0 else 0,
            "click_rate": (emails_clicked / emails_delivered * 100) if emails_delivered > 0 else 0,
            "reply_rate": (emails_replied / emails_delivered * 100) if emails_delivered > 0 else 0,
            "prospects_analyzed": campaign.get("prospects_analyzed", 0),
            "leads_qualified": campaign.get("leads_qualified", 0),
            "meetings_booked": campaign.get("meetings_booked", 0),
            "pipeline_value": campaign.get("pipeline_value", 0)
        }

    def _aggregate_metrics(self, campaigns: List[Dict]) -> Dict:
        """Aggregate metrics across multiple campaigns"""
        total = {
            "total_campaigns": len(campaigns),
            "active_campaigns": sum(1 for c in campaigns if c.get("status") == "active"),
            "emails_sent": 0,
            "emails_delivered": 0,
            "emails_opened": 0,
            "emails_clicked": 0,
            "emails_replied": 0,
            "prospects_analyzed": 0,
            "companies_researched": 0,
            "icp_matches": 0,
            "conversations_active": 0,
            "leads_qualified": 0,
            "meetings_booked": 0,
            "pipeline_value": 0,
            "closed_deals": 0,
            "revenue_generated": 0
        }

        for campaign in campaigns:
            total["emails_sent"] += campaign.get("emails_sent", 0)
            total["emails_delivered"] += campaign.get("emails_delivered", 0)
            total["emails_opened"] += campaign.get("emails_opened", 0)
            total["emails_clicked"] += campaign.get("emails_clicked", 0)
            total["emails_replied"] += campaign.get("emails_replied", 0)
            total["prospects_analyzed"] += campaign.get("prospects_analyzed", 0)
            total["companies_researched"] += campaign.get("companies_researched", 0)
            total["icp_matches"] += campaign.get("icp_matches", 0)
            total["conversations_active"] += campaign.get("conversations_active", 0)
            total["leads_qualified"] += campaign.get("leads_qualified", 0)
            total["meetings_booked"] += campaign.get("meetings_booked", 0)
            total["pipeline_value"] += campaign.get("pipeline_value", 0)
            total["closed_deals"] += campaign.get("closed_deals", 0)
            total["revenue_generated"] += campaign.get("revenue_generated", 0)

        # Calculate aggregate rates
        if total["emails_delivered"] > 0:
            total["open_rate"] = (total["emails_opened"] / total["emails_delivered"]) * 100
            total["click_rate"] = (total["emails_clicked"] / total["emails_delivered"]) * 100
            total["reply_rate"] = (total["emails_replied"] / total["emails_delivered"]) * 100
        else:
            total["open_rate"] = 0
            total["click_rate"] = 0
            total["reply_rate"] = 0

        return total

    def _get_date_metrics(self, date) -> Dict:
        """Get metrics for a specific date"""
        # TODO: Implement date-specific metrics from time-series data
        return {
            "emails_sent": 0,
            "leads_generated": 0,
            "meetings_booked": 0
        }

    def _empty_metrics(self) -> Dict:
        """Return empty metrics structure"""
        return {
            "total_campaigns": 0,
            "active_campaigns": 0,
            "emails_sent": 0,
            "emails_delivered": 0,
            "emails_opened": 0,
            "emails_clicked": 0,
            "emails_replied": 0,
            "open_rate": 0,
            "click_rate": 0,
            "reply_rate": 0,
            "prospects_analyzed": 0,
            "companies_researched": 0,
            "icp_matches": 0,
            "conversations_active": 0,
            "leads_qualified": 0,
            "meetings_booked": 0,
            "pipeline_value": 0,
            "closed_deals": 0,
            "revenue_generated": 0
        }


# Global dashboard instance
dashboard = MarketingDashboard()


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve marketing dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Marketing Engine - Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                line-height: 1.6;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }

            header {
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            }

            h1 {
                color: #667eea;
                font-size: 2.5em;
                margin-bottom: 10px;
            }

            .subtitle {
                color: #666;
                font-size: 1.1em;
            }

            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }

            .metric-card {
                background: rgba(255, 255, 255, 0.95);
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }

            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
            }

            .metric-title {
                font-size: 0.9em;
                color: #888;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }

            .metric-value {
                font-size: 2.5em;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }

            .metric-change {
                font-size: 0.9em;
                color: #28a745;
            }

            .metric-change.negative {
                color: #dc3545;
            }

            .channel-section {
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            }

            .channel-section h2 {
                color: #667eea;
                margin-bottom: 20px;
                font-size: 1.8em;
            }

            .channel-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
            }

            .channel-card {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }

            .channel-name {
                font-weight: bold;
                color: #667eea;
                margin-bottom: 15px;
                font-size: 1.2em;
            }

            .channel-metrics {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .channel-metric {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .channel-metric-label {
                color: #666;
                font-size: 0.9em;
            }

            .channel-metric-value {
                font-weight: bold;
                color: #333;
            }

            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
                overflow: hidden;
                margin-top: 5px;
            }

            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                transition: width 0.3s ease;
            }

            .refresh-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 25px;
                font-size: 1em;
                cursor: pointer;
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
                transition: all 0.3s ease;
            }

            .refresh-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.6);
            }

            .status-badge {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: bold;
                margin-left: 10px;
            }

            .status-operational {
                background: #28a745;
                color: white;
            }

            .loading {
                text-align: center;
                padding: 40px;
                color: white;
                font-size: 1.2em;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            .loading::after {
                content: '...';
                animation: pulse 1.5s infinite;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🚀 AI Marketing Engine Dashboard</h1>
                <p class="subtitle">Real-time campaign analytics and performance metrics
                    <span class="status-badge status-operational">100% OPERATIONAL</span>
                </p>
            </header>

            <div id="loading" class="loading">Loading dashboard data</div>

            <div id="dashboard" style="display: none;">
                <!-- Overview Metrics -->
                <div class="metrics-grid" id="overview-metrics"></div>

                <!-- Channel Performance -->
                <div class="channel-section">
                    <h2>📊 Channel Performance</h2>
                    <div class="channel-grid" id="channel-performance"></div>
                </div>

                <!-- AI Agents Activity -->
                <div class="channel-section">
                    <h2>🤖 AI Agents Activity</h2>
                    <div class="channel-grid" id="ai-agents"></div>
                </div>

                <!-- Revenue Metrics -->
                <div class="channel-section">
                    <h2>💰 Revenue & Pipeline</h2>
                    <div class="channel-grid" id="revenue-metrics"></div>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <button class="refresh-btn" onclick="loadDashboard()">🔄 Refresh Dashboard</button>
                </div>
            </div>
        </div>

        <script>
            async function loadDashboard() {
                try {
                    document.getElementById('loading').style.display = 'block';
                    document.getElementById('dashboard').style.display = 'none';

                    // Fetch metrics
                    const metricsRes = await fetch('/api/marketing/dashboard/metrics');
                    const metrics = await metricsRes.json();

                    // Fetch channel performance
                    const channelsRes = await fetch('/api/marketing/dashboard/channels');
                    const channels = await channelsRes.json();

                    // Render overview metrics
                    renderOverviewMetrics(metrics);

                    // Render channel performance
                    renderChannelPerformance(channels);

                    // Render AI agents
                    renderAIAgents(channels);

                    // Render revenue metrics
                    renderRevenueMetrics(metrics);

                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('dashboard').style.display = 'block';
                } catch (error) {
                    console.error('Failed to load dashboard:', error);
                    document.getElementById('loading').innerHTML = '❌ Failed to load dashboard. Please refresh.';
                }
            }

            function renderOverviewMetrics(metrics) {
                const container = document.getElementById('overview-metrics');
                container.innerHTML = `
                    <div class="metric-card">
                        <div class="metric-title">Total Campaigns</div>
                        <div class="metric-value">${metrics.total_campaigns}</div>
                        <div class="metric-change">+${metrics.active_campaigns} active</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Emails Sent</div>
                        <div class="metric-value">${metrics.emails_sent.toLocaleString()}</div>
                        <div class="metric-change">${metrics.emails_delivered.toLocaleString()} delivered</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Open Rate</div>
                        <div class="metric-value">${metrics.open_rate.toFixed(1)}%</div>
                        <div class="metric-change ${metrics.open_rate > 20 ? '' : 'negative'}">
                            ${metrics.open_rate > 20 ? '✓ Above average' : '⚠ Below average'}
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Leads Qualified</div>
                        <div class="metric-value">${metrics.leads_qualified}</div>
                        <div class="metric-change">${metrics.meetings_booked} meetings booked</div>
                    </div>
                `;
            }

            function renderChannelPerformance(channels) {
                const container = document.getElementById('channel-performance');
                const email = channels.email;

                container.innerHTML = `
                    <div class="channel-card">
                        <div class="channel-name">📧 Email Outreach</div>
                        <div class="channel-metrics">
                            <div class="channel-metric">
                                <span class="channel-metric-label">Sent</span>
                                <span class="channel-metric-value">${email.sent.toLocaleString()}</span>
                            </div>
                            <div class="channel-metric">
                                <span class="channel-metric-label">Delivered</span>
                                <span class="channel-metric-value">${email.delivered.toLocaleString()}</span>
                            </div>
                            <div class="channel-metric">
                                <span class="channel-metric-label">Opened</span>
                                <span class="channel-metric-value">${email.opened.toLocaleString()} (${email.open_rate.toFixed(1)}%)</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${email.open_rate}%"></div>
                            </div>
                            <div class="channel-metric">
                                <span class="channel-metric-label">Clicked</span>
                                <span class="channel-metric-value">${email.clicked.toLocaleString()} (${email.click_rate.toFixed(1)}%)</span>
                            </div>
                            <div class="channel-metric">
                                <span class="channel-metric-label">Replied</span>
                                <span class="channel-metric-value">${email.replied.toLocaleString()} (${email.reply_rate.toFixed(1)}%)</span>
                            </div>
                        </div>
                    </div>
                `;
            }

            function renderAIAgents(channels) {
                const container = document.getElementById('ai-agents');
                const research = channels.ai_research;
                const conversation = channels.ai_conversation;

                container.innerHTML = `
                    <div class="channel-card">
                        <div class="channel-name">🔍 Research AI</div>
                        <div class="channel-metrics">
                            <div class="channel-metric">
                                <span class="channel-metric-label">Prospects Analyzed</span>
                                <span class="channel-metric-value">${research.prospects_analyzed.toLocaleString()}</span>
                            </div>
                            <div class="channel-metric">
                                <span class="channel-metric-label">Companies Researched</span>
                                <span class="channel-metric-value">${research.companies_researched.toLocaleString()}</span>
                            </div>
                            <div class="channel-metric">
                                <span class="channel-metric-label">ICP Matches</span>
                                <span class="channel-metric-value">${research.icp_matches.toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                    <div class="channel-card">
                        <div class="channel-name">💬 Conversation AI</div>
                        <div class="channel-metrics">
                            <div class="channel-metric">
                                <span class="channel-metric-label">Active Conversations</span>
                                <span class="channel-metric-value">${conversation.conversations_active}</span>
                            </div>
                            <div class="channel-metric">
                                <span class="channel-metric-label">Leads Qualified</span>
                                <span class="channel-metric-value">${conversation.leads_qualified}</span>
                            </div>
                            <div class="channel-metric">
                                <span class="channel-metric-label">Meetings Booked</span>
                                <span class="channel-metric-value">${conversation.meetings_booked}</span>
                            </div>
                        </div>
                    </div>
                `;
            }

            function renderRevenueMetrics(metrics) {
                const container = document.getElementById('revenue-metrics');
                container.innerHTML = `
                    <div class="channel-card">
                        <div class="channel-name">💼 Pipeline Value</div>
                        <div class="channel-metrics">
                            <div class="channel-metric">
                                <span class="channel-metric-label">Total Pipeline</span>
                                <span class="channel-metric-value">$${metrics.pipeline_value.toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                    <div class="channel-card">
                        <div class="channel-name">🎯 Closed Deals</div>
                        <div class="channel-metrics">
                            <div class="channel-metric">
                                <span class="channel-metric-label">Total Deals</span>
                                <span class="channel-metric-value">${metrics.closed_deals}</span>
                            </div>
                        </div>
                    </div>
                    <div class="channel-card">
                        <div class="channel-name">💰 Revenue Generated</div>
                        <div class="channel-metrics">
                            <div class="channel-metric">
                                <span class="channel-metric-label">Total Revenue</span>
                                <span class="channel-metric-value">$${metrics.revenue_generated.toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                `;
            }

            // Load dashboard on page load
            loadDashboard();

            // Auto-refresh every 30 seconds
            setInterval(loadDashboard, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/dashboard/metrics")
async def get_metrics():
    """Get overall marketing metrics"""
    return dashboard.get_campaign_metrics()


@router.get("/dashboard/channels")
async def get_channel_performance():
    """Get performance by channel"""
    return dashboard.get_channel_performance()


@router.get("/dashboard/daily-report")
async def get_daily_report():
    """Get marketing data for daily report"""
    return dashboard.get_daily_report_data()


@router.get("/dashboard/campaign/{campaign_id}")
async def get_campaign_metrics(campaign_id: str):
    """Get metrics for specific campaign"""
    metrics = dashboard.get_campaign_metrics(campaign_id)
    if not metrics or metrics.get("campaign_id") is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return metrics
