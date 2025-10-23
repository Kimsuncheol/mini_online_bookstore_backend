"""
Member Model

Defines the Pydantic model for member (user) data with validation and serialization.
Aligned with the client-side User interface from BookNest application.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserPreferences(BaseModel):
    """User notification and marketing preferences."""

    email_notifications: bool = Field(default=True, description="Enable email notifications")
    marketing_emails: bool = Field(default=False, description="Enable marketing emails")


class MemberBase(BaseModel):
    """Base member model with common fields."""

    email: EmailStr = Field(..., description="Member email address")
    display_name: Optional[str] = Field(None, max_length=255, description="Member display name")
    photo_url: Optional[str] = Field(None, description="Member profile photo URL")
    phone: Optional[str] = Field(None, max_length=20, description="Member phone number")
    address: Optional[str] = Field(None, description="Member address")


class MemberCreate(MemberBase):
    """Member model for creating new members."""

    pass


class MemberUpdate(BaseModel):
    """Member model for updating existing members."""

    email: Optional[EmailStr] = Field(None, description="Member email address")
    display_name: Optional[str] = Field(None, max_length=255, description="Member display name")
    photo_url: Optional[str] = Field(None, description="Member profile photo URL")
    phone: Optional[str] = Field(None, max_length=20, description="Member phone number")
    address: Optional[str] = Field(None, description="Member address")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences")


class Member(MemberBase):
    """
    Complete member model with authentication and account metadata.

    Represents a user in the BookNest application with all their profile information,
    account status, and preferences aligned with the client-side User interface.
    """

    # Authentication
    id: str = Field(..., description="Unique member identifier (Firestore document ID)")

    # Account Status
    is_email_verified: bool = Field(default=False, description="Email verification status")
    created_at: datetime = Field(..., description="Member account creation timestamp")
    last_sign_in_at: Optional[datetime] = Field(None, description="Member last sign-in timestamp")

    # User Preferences
    preferences: Optional[UserPreferences] = Field(None, description="User notification preferences")

    class Config:
        """Pydantic configuration."""

        from_attributes = True  # Allow population by field name
        populate_by_name = True  # Allow both snake_case and camelCase
