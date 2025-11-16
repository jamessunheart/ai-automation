"""Email sending service with SendGrid integration"""

import os
from typing import Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email sending service using SendGrid API

    Handles:
    - Sending personalized emails
    - Tracking opens/clicks
    - Managing send rate limits
    - Email validation
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize email service with SendGrid API key"""
        self.api_key = api_key or os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'james@fullpotential.com')
        self.from_name = os.getenv('SENDGRID_FROM_NAME', 'James from Full Potential AI')

        # Track daily send count for rate limiting
        self.daily_send_count = 0
        self.daily_limit = int(os.getenv('SENDGRID_DAILY_LIMIT', '500'))

        # Initialize SendGrid client if API key available
        self.sg = None
        if self.api_key:
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail
                self.sg = SendGridAPIClient(self.api_key)
                self.Mail = Mail
                logger.info("✅ SendGrid initialized successfully")
            except ImportError:
                logger.warning("⚠️  SendGrid not installed. Run: pip install sendgrid")
            except Exception as e:
                logger.error(f"❌ SendGrid initialization failed: {e}")
        else:
            logger.warning("⚠️  SENDGRID_API_KEY not set. Email sending will be simulated.")


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
        track_clicks: bool = True
    ) -> Dict:
        """
        Send a personalized email

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject line
            body_html: HTML email body
            body_text: Plain text email body (optional, auto-generated if not provided)
            reply_to: Reply-to email (defaults to from_email)
            custom_args: Custom tracking arguments (prospect_id, campaign_id, etc.)
            track_opens: Enable open tracking
            track_clicks: Enable click tracking

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

        # If SendGrid not available, simulate send
        if not self.sg:
            logger.info(f"📧 [SIMULATED] Sending email to {to_name} <{to_email}>")
            logger.info(f"   Subject: {subject}")
            return {
                "success": True,
                "simulated": True,
                "to": to_email,
                "subject": subject,
                "timestamp": datetime.utcnow().isoformat()
            }

        try:
            # Create email message
            message = self.Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=(to_email, to_name),
                subject=subject,
                html_content=body_html,
                plain_text_content=body_text or self._html_to_text(body_html)
            )

            # Set reply-to
            if reply_to:
                message.reply_to = reply_to

            # Add tracking settings
            message.tracking_settings = {
                "click_tracking": {
                    "enable": track_clicks,
                    "enable_text": False
                },
                "open_tracking": {
                    "enable": track_opens
                }
            }

            # Add custom tracking arguments
            if custom_args:
                message.custom_arg = custom_args

            # Send email
            response = self.sg.send(message)

            # Increment daily counter
            self.daily_send_count += 1

            logger.info(f"✅ Email sent to {to_name} <{to_email}> - Status: {response.status_code}")

            return {
                "success": True,
                "to": to_email,
                "subject": subject,
                "status_code": response.status_code,
                "message_id": response.headers.get('X-Message-Id'),
                "timestamp": datetime.utcnow().isoformat(),
                "daily_count": self.daily_send_count
            }

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email
            }


    def send_bulk_emails(
        self,
        emails: List[Dict],
        delay_seconds: float = 2.0
    ) -> Dict:
        """
        Send multiple emails with rate limiting

        Args:
            emails: List of email dicts with {to_email, to_name, subject, body_html, ...}
            delay_seconds: Delay between emails to avoid rate limits

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

        logger.info(f"📊 Bulk send complete: {results['sent']} sent, {results['failed']} failed, {results['skipped']} skipped")

        return results


    def personalize_template(
        self,
        template: str,
        variables: Dict
    ) -> str:
        """
        Replace template variables with actual values

        Args:
            template: Template string with {{variable}} placeholders
            variables: Dict of variable_name: value

        Returns:
            Personalized string
        """
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
        """Convert HTML to plain text (basic implementation)"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text


    def get_send_stats(self) -> Dict:
        """Get current sending statistics"""
        return {
            "daily_count": self.daily_send_count,
            "daily_limit": self.daily_limit,
            "remaining": self.daily_limit - self.daily_send_count,
            "percentage_used": round((self.daily_send_count / self.daily_limit) * 100, 2)
        }


    def reset_daily_counter(self):
        """Reset daily send counter (called at midnight UTC)"""
        self.daily_send_count = 0
        logger.info("🔄 Daily send counter reset")


# Global email service instance
_email_service = None


def get_email_service() -> EmailService:
    """Get or create global email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
