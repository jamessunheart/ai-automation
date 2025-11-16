"""Data models for marketing engine"""

from .prospect import (
    Prospect,
    ProspectStatus,
    ProspectScore,
    Campaign,
    EmailTemplate
)

__all__ = [
    "Prospect",
    "ProspectStatus",
    "ProspectScore",
    "Campaign",
    "EmailTemplate"
]
