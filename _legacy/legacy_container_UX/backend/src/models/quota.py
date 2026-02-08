"""Quota usage models."""

from datetime import datetime
from pydantic import BaseModel, Field


class DailyUsage(BaseModel):
    """Daily quota usage record."""

    date: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    quota_used: int = Field(..., ge=0, description="Quota units consumed")
    quota_limit: int = Field(..., ge=0, description="Daily quota limit")
    tier: str = Field(..., description="User tier on this date")


class QuotaUsageSummary(BaseModel):
    """Aggregated quota usage summary."""

    user_id: str
    start_date: datetime
    end_date: datetime
    total_used: int = Field(ge=0, description="Total quota consumed in period")
    total_limit: int = Field(ge=0, description="Total quota available in period")
    remaining: int = Field(ge=0, description="Quota remaining")
    breakdown_by_day: list[dict] = Field(default_factory=list, description="Daily breakdown")
