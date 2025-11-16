"""Email sending service with Brevo (SendinBlue) integration"""

import os
from typing import Optional, Dict, List
from datetime import datetime
import logging
import requests

logger = logging.getLogger(__name__)


class BrevoEmailService:
    """
    Email sending service using Brevo (formerly SendinBlue) API

    Brevo API Documentation: https://developers.brevo.com/

    Handles:
    - Sending personalized emails via SMTP API
    - Tracking opens/clicks
    - Managing send rate limits
    - Email validation
    - Template personalization
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Brevo email service"""
        self.api_key = api_key or os.getenv('BREVO_API_KEY')
        self.from_email = os.getenv('BREVO_FROM_EMAIL', os.getenv('SENDGRID_FROM_EMAIL', 'james@fullpotential.com'))
        self.from_name = os.getenv('BREVO_FROM_NAME', os.getenv('SENDGRID_FROM_NAME', 'James from Full Potential AI'))

        # Brevo API endpoint
        self.api_url = "https://api.brevo.com/v3/smtp/email"

        # Track daily send count for rate limiting
        self.daily_send_count = 0
        # Brevo free tier: 300 emails/day, paid starts at 20,000/day
        self.daily_limit = int(os.getenv('BREVO_DAILY_LIMIT', '300'))

        # Set up headers
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        if self.api_key:
            self.headers["api-key"] = self.api_key
            logger.info("✅ Brevo initialized successfully")
        else:
            logger.warning("⚠️  BREVO_API_KEY not set. Email sending will be simulated.")


    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        reply_to: Optional[str] = None,
        custom_args: Optional[Dict] = None,
        track_opens: bool = True,
        track_clicks: bool = True,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Send a personalized email via Brevo

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject line
            body_html: HTML email body
            body_text: Plain text email body (optional)
            reply_to: Reply-to email (defaults to from_email)
            custom_args: Custom tracking parameters
            track_opens: Enable open tracking
            track_clicks: Enable click tracking
            tags: Email tags for organization (max 10)

        Returns:
            Dict with send status and tracking info
        """

        # Check rate limits
        if self.daily_send_count >= self.daily_limit:
            logger.warning(f"⚠️  Daily send limit reached ({self.daily_limit})")
            return {
                "success": False,
                "error": "Daily send limit reached",
                "daily_count": self.daily_send_count
            }

        # Validate email
        if not self._validate_email(to_email):
            logger.error(f"❌ Invalid email address: {to_email}")
            return {
                "success": False,
                "error": "Invalid email address"
            }

        # If Brevo not configured, simulate send
        if not self.api_key:
            logger.info(f"📧 [SIMULATED - BREVO] Sending email to {to_name} <{to_email}>")
            logger.info(f"   Subject: {subject}")
            return {
                "success": True,
                "simulated": True,
                "provider": "brevo",
                "to": to_email,
                "subject": subject,
                "timestamp": datetime.utcnow().isoformat()
            }

        try:
            # Build Brevo email payload
            payload = {
                "sender": {
                    "name": self.from_name,
                    "email": self.from_email
                },
                "to": [
                    {
                        "email": to_email,
                        "name": to_name
                    }
                ],
                "subject": subject,
                "htmlContent": body_html
            }

            # Add plain text if provided
            if body_text:
                payload["textContent"] = body_text
            else:
                payload["textContent"] = self._html_to_text(body_html)

            # Set reply-to
            if reply_to:
                payload["replyTo"] = {
                    "email": reply_to
                }

            # Add tracking params
            if custom_args:
                payload["params"] = custom_args

            # Add tags if provided
            if tags:
                payload["tags"] = tags[:10]  # Max 10 tags

            # Tracking settings (Brevo has these enabled by default)
            # Can be disabled per email if needed
            payload["trackOpens"] = track_opens
            payload["trackClicks"] = track_clicks

            # Send email via Brevo API
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )

            # Check response
            if response.status_code in [200, 201]:
                result = response.json()
                self.daily_send_count += 1

                logger.info(f"✅ Email sent via Brevo to {to_name} <{to_email}> - Message ID: {result.get('messageId')}")

                return {
                    "success": True,
                    "provider": "brevo",
                    "to": to_email,
                    "subject": subject,
                    "message_id": result.get("messageId"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "daily_count": self.daily_send_count
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                logger.error(f"❌ Brevo API error: {response.status_code} - {error_msg}")
                return {
                    "success": False,
                    "error": f"Brevo API error: {error_msg}",
                    "status_code": response.status_code
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email
            }


    def send_bulk_emails(
        self,
        emails: List[Dict],
        delay_seconds: float = 1.0
    ) -> Dict:
        """
        Send multiple emails with rate limiting

        Args:
            emails: List of email dicts
            delay_seconds: Delay between emails

        Returns:
            Dict with send statistics
        """
        import time

        results = {
            "total": len(emails),
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }

        for email_data in emails:
            # Check rate limit
            if self.daily_send_count >= self.daily_limit:
                results["skipped"] = results["total"] - results["sent"] - results["failed"]
                logger.warning(f"⚠️  Stopping bulk send - daily limit reached")
                break

            # Send email
            result = self.send_email(**email_data)

            if result.get("success"):
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "email": email_data.get("to_email"),
                    "error": result.get("error")
                })

            # Delay between sends
            if delay_seconds > 0:
                time.sleep(delay_seconds)

        logger.info(f"📊 Brevo bulk send complete: {results['sent']} sent, {results['failed']} failed, {results['skipped']} skipped")

        return results


    def personalize_template(
        self,
        template: str,
        variables: Dict
    ) -> str:
        """Replace template variables"""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result


    def _validate_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        import re
        text = re.sub(r'<[^>]+>', '', html)
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = re.sub(r'\s+', ' ', text).strip()
        return text


    def get_send_stats(self) -> Dict:
        """Get current sending statistics"""
        return {
            "provider": "brevo",
            "daily_count": self.daily_send_count,
            "daily_limit": self.daily_limit,
            "remaining": self.daily_limit - self.daily_send_count,
            "percentage_used": round((self.daily_send_count / self.daily_limit) * 100, 2)
        }


    def reset_daily_counter(self):
        """Reset daily send counter"""
        self.daily_send_count = 0
        logger.info("🔄 Daily send counter reset")


# Global Brevo email service instance
_brevo_service = None


def get_brevo_service() -> BrevoEmailService:
    """Get or create global Brevo email service instance"""
    global _brevo_service
    if _brevo_service is None:
        _brevo_service = BrevoEmailService()
    return _brevo_service
