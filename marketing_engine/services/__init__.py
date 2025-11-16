"""Services for marketing engine"""

# Using Brevo email service (SendGrid replacement)
from .email_service_brevo import BrevoEmailService as EmailService, get_brevo_service as get_email_service

__all__ = [
    "EmailService",
    "get_email_service"
]
