"""
Coupon Model

Defines the Pydantic models for coupon management.
Handles coupon creation, usage, and tracking.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr


class CouponCreate(BaseModel):
    """Model for creating a new coupon."""

    code: str = Field(..., max_length=50, description="Unique coupon code")
    discount_value: float = Field(
        ..., gt=0, description="Discount value in dollars"
    )
    source: Literal["check_in", "promotion", "manual"] = Field(
        default="manual", description="Source of the coupon"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Coupon description"
    )
    expiration_date: Optional[str] = Field(
        None, description="Expiration date (YYYY-MM-DD format)"
    )


class CouponUpdate(BaseModel):
    """Model for updating an existing coupon."""

    code: Optional[str] = Field(None, max_length=50, description="Coupon code")
    discount_value: Optional[float] = Field(
        None, gt=0, description="Discount value in dollars"
    )
    source: Optional[Literal["check_in", "promotion", "manual"]] = Field(
        None, description="Source of the coupon"
    )
    description: Optional[str] = Field(None, max_length=500, description="Description")
    used: Optional[bool] = Field(None, description="Whether coupon has been used")
    used_date: Optional[str] = Field(None, description="Date coupon was used")
    expiration_date: Optional[str] = Field(None, description="Expiration date")
    issued: Optional[bool] = Field(None, description="Whether coupon has been issued")
    issued_date: Optional[str] = Field(None, description="Date coupon was issued")


class CouponBase(BaseModel):
    """Base coupon model with common fields."""

    code: str = Field(..., max_length=50, description="Unique coupon code")
    user_email: EmailStr = Field(..., description="User's email address")
    discount_value: float = Field(..., gt=0, description="Discount value in dollars")
    source: Literal["check_in", "promotion", "manual"] = Field(
        default="manual", description="Source of the coupon"
    )
    description: Optional[str] = Field(None, description="Coupon description")
    used: bool = Field(default=False, description="Whether coupon has been used")
    used_date: Optional[str] = Field(None, description="Date coupon was used")
    issued: bool = Field(default=False, description="Whether coupon has been issued")
    issued_date: Optional[str] = Field(None, description="Date coupon was issued")
    expiration_date: Optional[str] = Field(None, description="Expiration date")


class Coupon(CouponBase):
    """
    Complete coupon model with metadata.

    Represents a coupon in the database.
    """

    id: str = Field(..., description="Unique coupon ID (Firestore document ID)")
    created_at: datetime = Field(..., description="Coupon creation timestamp")
    updated_at: datetime = Field(..., description="Coupon last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True


class CouponSummary(BaseModel):
    """Summary model for coupon listings."""

    id: str = Field(..., description="Coupon ID")
    code: str = Field(..., description="Coupon code")
    discount_value: float = Field(..., description="Discount value")
    source: str = Field(..., description="Coupon source")
    used: bool = Field(..., description="Whether coupon is used")
    issued: bool = Field(..., description="Whether coupon is issued")
    expiration_date: Optional[str] = Field(None, description="Expiration date")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class CouponIssueRecord(BaseModel):
    """Model for tracking coupon issue records for streak milestones."""

    user_id: str = Field(..., description="User ID")
    user_email: EmailStr = Field(..., description="User's email address")
    streak_days: int = Field(..., ge=7, description="Streak days (7, 14, 30, etc)")
    coupon_value: float = Field(..., gt=0, description="Coupon value in dollars")
    coupon_id: Optional[str] = Field(
        None, description="ID of the issued coupon"
    )
    issued: bool = Field(default=False, description="Whether coupon has been issued")
    issued_at: Optional[datetime] = Field(None, description="When coupon was issued")


class CouponIssueRecordResponse(BaseModel):
    """Response model for coupon issue records."""

    id: str = Field(..., description="Record ID")
    user_id: str = Field(..., description="User ID")
    user_email: str = Field(..., description="User's email")
    streak_days: int = Field(..., description="Streak days")
    coupon_value: float = Field(..., description="Coupon value")
    coupon_id: Optional[str] = Field(None, description="Coupon ID if issued")
    issued: bool = Field(..., description="Whether coupon is issued")
    issued_at: Optional[datetime] = Field(None, description="Issue timestamp")
    created_at: datetime = Field(..., description="Record creation timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class CouponResponse(BaseModel):
    """Generic coupon response model."""

    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Response message")
    coupon: Optional[Coupon] = Field(None, description="Coupon data if applicable")
    coupons: Optional[list[Coupon]] = Field(
        None, description="List of coupons if applicable"
    )
    count: Optional[int] = Field(None, description="Count of coupons if applicable")


__all__ = [
    "CouponCreate",
    "CouponUpdate",
    "CouponBase",
    "Coupon",
    "CouponSummary",
    "CouponIssueRecord",
    "CouponIssueRecordResponse",
    "CouponResponse",
]
