"""
Check-In Model

Defines the Pydantic models for user check-in functionality.
Handles daily check-in tracking, streak management, and coupon earning.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class CheckInRecord(BaseModel):
    """Model for a single daily check-in record."""

    date: str = Field(..., description="Date of check-in (YYYY-MM-DD format)")
    checked_in: bool = Field(
        default=True, description="Whether user checked in on this date"
    )


class CheckInStats(BaseModel):
    """User's check-in statistics."""

    current_streak: int = Field(
        default=0, description="Current consecutive check-in days"
    )
    longest_streak: int = Field(
        default=0, description="Longest streak achieved"
    )
    total_check_ins: int = Field(
        default=0, description="Total number of check-ins"
    )
    last_check_in_date: Optional[str] = Field(
        None, description="Last check-in date (YYYY-MM-DD format)"
    )


class CheckInBase(BaseModel):
    """Base check-in model with common fields."""

    user_id: str = Field(..., description="User ID")
    user_email: EmailStr = Field(..., description="User's email address")
    user_name: str = Field(..., description="User's display name")
    current_streak: int = Field(default=0, description="Current streak count")
    longest_streak: int = Field(default=0, description="Longest streak achieved")
    total_check_ins: int = Field(default=0, description="Total check-ins count")
    checked_in_today: bool = Field(
        default=False, description="Whether user checked in today"
    )
    last_check_in_date: Optional[str] = Field(
        None, description="Last check-in date (YYYY-MM-DD format)"
    )


class CheckInCreate(CheckInBase):
    """Check-in model for creating/updating check-in records."""

    pass


class CheckInUpdate(BaseModel):
    """Check-in model for updating check-in records."""

    current_streak: Optional[int] = Field(None, description="Current streak count")
    longest_streak: Optional[int] = Field(None, description="Longest streak")
    total_check_ins: Optional[int] = Field(None, description="Total check-ins")
    checked_in_today: Optional[bool] = Field(None, description="Checked in today flag")
    last_check_in_date: Optional[str] = Field(None, description="Last check-in date")


class CheckIn(CheckInBase):
    """
    Complete check-in model with metadata.

    Represents a user's check-in record in the database.
    """

    id: str = Field(..., description="Unique check-in record ID (Firestore document ID)")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True


class CheckInResponse(BaseModel):
    """Response model for check-in operations."""

    success: bool = Field(..., description="Whether check-in was successful")
    message: str = Field(..., description="Response message")
    stats: Optional[CheckInStats] = Field(None, description="Updated check-in statistics")
    earned_coupons: Optional[List[dict]] = Field(
        None, description="Coupons earned from this check-in"
    )
    checked_in_today: bool = Field(
        default=False, description="Whether user checked in today"
    )


class CheckInProfile(BaseModel):
    """Complete check-in profile for a user."""

    user_id: str = Field(..., description="User ID")
    user_email: str = Field(..., description="User's email")
    user_name: str = Field(..., description="User's display name")
    stats: CheckInStats = Field(..., description="Check-in statistics")
    recent_records: List[CheckInRecord] = Field(
        default=[], description="Recent check-in records"
    )
    coupons: List[dict] = Field(default=[], description="Earned coupons")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Profile last update timestamp")


__all__ = [
    "CheckInRecord",
    "CheckInStats",
    "CheckInBase",
    "CheckInCreate",
    "CheckInUpdate",
    "CheckIn",
    "CheckInResponse",
    "CheckInProfile",
]
