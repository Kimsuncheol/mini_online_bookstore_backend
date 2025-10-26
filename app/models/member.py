"""
User Model

Defines the Pydantic models that mirror the client-side `User` interface used
by the BookNest application. These models provide validation, alias handling
between snake_case and camelCase, and serialization helpers.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, EmailStr, Field


class UserPreferences(BaseModel):
    """User notification and marketing preferences."""

    email_notifications: bool = Field(
        default=True,
        description="Enable email notifications",
        alias="emailNotifications",
        validation_alias=AliasChoices("emailNotifications", "email_notifications"),
        serialization_alias="emailNotifications",
    )
    marketing_emails: bool = Field(
        default=False,
        description="Enable marketing emails",
        alias="marketingEmails",
        validation_alias=AliasChoices("marketingEmails", "marketing_emails"),
        serialization_alias="marketingEmails",
    )

    class Config:
        """Allow population using either snake_case or camelCase."""

        populate_by_name = True


class UserBase(BaseModel):
    """Base user model with core profile fields shared across operations."""

    email: EmailStr = Field(..., description="User email address")
    display_name: Optional[str] = Field(
        None,
        max_length=255,
        description="User display name",
        alias="displayName",
        validation_alias=AliasChoices("displayName", "display_name"),
        serialization_alias="displayName",
    )
    photo_url: Optional[str] = Field(
        None,
        description="User profile photo URL",
        alias="photoURL",
        validation_alias=AliasChoices("photoURL", "photo_url"),
        serialization_alias="photoURL",
    )
    role: Literal["admin", "author", "user"] = Field(
        default="user",
        description="User role defining permissions",
    )
    is_email_verified: bool = Field(
        default=False,
        description="Email verification status",
        alias="isEmailVerified",
        validation_alias=AliasChoices("isEmailVerified", "is_email_verified"),
        serialization_alias="isEmailVerified",
    )
    phone: Optional[str] = Field(None, max_length=20, description="User phone number")
    address: Optional[str] = Field(None, description="User address")
    preferences: Optional[UserPreferences] = Field(
        None, description="User notification and marketing preferences"
    )

    class Config:
        """Allow population by field name for base model."""

        populate_by_name = True


class UserCreate(UserBase):
    """User model for creating new users."""

    created_at: Optional[datetime] = Field(
        None,
        description="User account creation timestamp",
        alias="createdAt",
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    last_sign_in_at: Optional[datetime] = Field(
        None,
        description="User last sign-in timestamp",
        alias="lastSignInAt",
        validation_alias=AliasChoices("lastSignInAt", "last_sign_in_at"),
        serialization_alias="lastSignInAt",
    )

    class Config:
        """Allow population by field name."""

        populate_by_name = True


class UserUpdate(BaseModel):
    """User model for updating existing users."""

    email: Optional[EmailStr] = Field(None, description="User email address")
    display_name: Optional[str] = Field(
        None,
        max_length=255,
        description="User display name",
        alias="displayName",
        validation_alias=AliasChoices("displayName", "display_name"),
        serialization_alias="displayName",
    )
    photo_url: Optional[str] = Field(
        None,
        description="User profile photo URL",
        alias="photoURL",
        validation_alias=AliasChoices("photoURL", "photo_url"),
        serialization_alias="photoURL",
    )
    role: Optional[Literal["admin", "author", "user"]] = Field(
        None, description="User role defining permissions"
    )
    is_email_verified: Optional[bool] = Field(
        None,
        description="Email verification status",
        alias="isEmailVerified",
        validation_alias=AliasChoices("isEmailVerified", "is_email_verified"),
        serialization_alias="isEmailVerified",
    )
    phone: Optional[str] = Field(None, max_length=20, description="User phone number")
    address: Optional[str] = Field(None, description="User address")
    preferences: Optional[UserPreferences] = Field(
        None, description="User notification and marketing preferences"
    )
    last_sign_in_at: Optional[datetime] = Field(
        None,
        description="User last sign-in timestamp",
        alias="lastSignInAt",
        validation_alias=AliasChoices("lastSignInAt", "last_sign_in_at"),
        serialization_alias="lastSignInAt",
    )

    class Config:
        """Allow population by field name."""

        populate_by_name = True


class User(UserBase):
    """
    Complete user model with authentication and account metadata.

    Represents a user in the BookNest application with all profile information,
    account status, and preferences aligned with the client-side User interface.
    """

    id: str = Field(..., description="Unique user identifier (Firestore document ID)")
    created_at: datetime = Field(
        ...,
        description="User account creation timestamp",
        alias="createdAt",
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    last_sign_in_at: Optional[datetime] = Field(
        None,
        description="User last sign-in timestamp",
        alias="lastSignInAt",
        validation_alias=AliasChoices("lastSignInAt", "last_sign_in_at"),
        serialization_alias="lastSignInAt",
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True  # Allow population by field name
        populate_by_name = True  # Allow both snake_case and camelCase


__all__ = ["UserPreferences", "UserBase", "UserCreate", "UserUpdate", "User"]
