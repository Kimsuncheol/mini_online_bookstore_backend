"""
Author Model

Defines the Pydantic models that mirror the client-side `Author` interface used
by the BookNest application. These models provide validation, alias handling
between snake_case and camelCase, and serialization helpers for author profiles.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, EmailStr, Field


class AuthorSocialLinks(BaseModel):
    """Author social media links."""

    twitter: Optional[str] = Field(
        None,
        description="Author Twitter handle",
    )
    facebook: Optional[str] = Field(
        None,
        description="Author Facebook profile",
    )
    instagram: Optional[str] = Field(
        None,
        description="Author Instagram profile",
    )
    linkedin: Optional[str] = Field(
        None,
        description="Author LinkedIn profile",
    )

    class Config:
        """Allow population using field name."""

        populate_by_name = True


class AuthorPreferences(BaseModel):
    """Author notification and marketing preferences."""

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


class AuthorBase(BaseModel):
    """Base author model with core profile fields."""

    email: EmailStr = Field(..., description="Author email address")
    display_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Author display name",
        alias="displayName",
        validation_alias=AliasChoices("displayName", "display_name"),
        serialization_alias="displayName",
    )
    photo_url: Optional[str] = Field(
        None,
        description="Author profile photo URL",
        alias="photoURL",
        validation_alias=AliasChoices("photoURL", "photo_url"),
        serialization_alias="photoURL",
    )
    is_email_verified: bool = Field(
        default=False,
        description="Email verification status",
        alias="isEmailVerified",
        validation_alias=AliasChoices("isEmailVerified", "is_email_verified"),
        serialization_alias="isEmailVerified",
    )
    bio: Optional[str] = Field(None, description="Author biography")
    website: Optional[str] = Field(None, description="Author website URL")
    social_links: Optional[AuthorSocialLinks] = Field(
        None,
        description="Author social media links",
        alias="socialLinks",
        validation_alias=AliasChoices("socialLinks", "social_links"),
        serialization_alias="socialLinks",
    )
    phone: Optional[str] = Field(None, max_length=20, description="Author phone number")
    address: Optional[str] = Field(None, description="Author address")

    class Config:
        """Allow population by field name for base model."""

        populate_by_name = True


class AuthorCreate(AuthorBase):
    """Author model for creating new authors."""

    created_at: Optional[datetime] = Field(
        None,
        description="Author account creation timestamp",
        alias="createdAt",
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    last_sign_in_at: Optional[datetime] = Field(
        None,
        description="Author last sign-in timestamp",
        alias="lastSignInAt",
        validation_alias=AliasChoices("lastSignInAt", "last_sign_in_at"),
        serialization_alias="lastSignInAt",
    )

    class Config:
        """Allow population by field name."""

        populate_by_name = True


class AuthorUpdate(BaseModel):
    """Author model for updating existing authors."""

    email: Optional[EmailStr] = Field(None, description="Author email address")
    display_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Author display name",
        alias="displayName",
        validation_alias=AliasChoices("displayName", "display_name"),
        serialization_alias="displayName",
    )
    photo_url: Optional[str] = Field(
        None,
        description="Author profile photo URL",
        alias="photoURL",
        validation_alias=AliasChoices("photoURL", "photo_url"),
        serialization_alias="photoURL",
    )
    is_email_verified: Optional[bool] = Field(
        None,
        description="Email verification status",
        alias="isEmailVerified",
        validation_alias=AliasChoices("isEmailVerified", "is_email_verified"),
        serialization_alias="isEmailVerified",
    )
    bio: Optional[str] = Field(None, description="Author biography")
    website: Optional[str] = Field(None, description="Author website URL")
    social_links: Optional[AuthorSocialLinks] = Field(
        None,
        description="Author social media links",
        alias="socialLinks",
        validation_alias=AliasChoices("socialLinks", "social_links"),
        serialization_alias="socialLinks",
    )
    phone: Optional[str] = Field(None, max_length=20, description="Author phone number")
    address: Optional[str] = Field(None, description="Author address")
    preferences: Optional[AuthorPreferences] = Field(
        None, description="Author notification and marketing preferences"
    )
    last_sign_in_at: Optional[datetime] = Field(
        None,
        description="Author last sign-in timestamp",
        alias="lastSignInAt",
        validation_alias=AliasChoices("lastSignInAt", "last_sign_in_at"),
        serialization_alias="lastSignInAt",
    )

    class Config:
        """Allow population by field name."""

        populate_by_name = True


class Author(AuthorBase):
    """
    Complete author model with authentication and account metadata.

    Represents an author in the BookNest application with all profile information,
    account status, author-specific fields, and preferences aligned with the client-side Author interface.
    """

    id: str = Field(..., description="Unique author identifier (Firestore document ID)")
    role: Literal["author"] = Field(
        default="author",
        description="Author role",
    )
    created_at: datetime = Field(
        ...,
        description="Author account creation timestamp",
        alias="createdAt",
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    last_sign_in_at: Optional[datetime] = Field(
        None,
        description="Author last sign-in timestamp",
        alias="lastSignInAt",
        validation_alias=AliasChoices("lastSignInAt", "last_sign_in_at"),
        serialization_alias="lastSignInAt",
    )
    is_verified: bool = Field(
        default=False,
        description="Author verification status",
        alias="isVerified",
        validation_alias=AliasChoices("isVerified", "is_verified"),
        serialization_alias="isVerified",
    )
    verification_date: Optional[datetime] = Field(
        None,
        description="Author verification date",
        alias="verificationDate",
        validation_alias=AliasChoices("verificationDate", "verification_date"),
        serialization_alias="verificationDate",
    )
    verification_badge: bool = Field(
        default=False,
        description="Whether author has a verification badge",
        alias="verificationBadge",
        validation_alias=AliasChoices("verificationBadge", "verification_badge"),
        serialization_alias="verificationBadge",
    )
    total_books_published: int = Field(
        default=0,
        ge=0,
        description="Total number of books published by author",
        alias="totalBooksPublished",
        validation_alias=AliasChoices("totalBooksPublished", "total_books_published"),
        serialization_alias="totalBooksPublished",
    )
    total_readers_reached: int = Field(
        default=0,
        ge=0,
        description="Total number of readers reached",
        alias="totalReadersReached",
        validation_alias=AliasChoices("totalReadersReached", "total_readers_reached"),
        serialization_alias="totalReadersReached",
    )
    average_rating: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Average rating of author's books",
        alias="averageRating",
        validation_alias=AliasChoices("averageRating", "average_rating"),
        serialization_alias="averageRating",
    )
    preferences: Optional[AuthorPreferences] = Field(
        None, description="Author notification and marketing preferences"
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True  # Allow population by field name
        populate_by_name = True  # Allow both snake_case and camelCase


class AuthorProfile(BaseModel):
    """Author profile data interface for public profile display."""

    id: str = Field(..., description="Unique author identifier")
    display_name: str = Field(
        ...,
        max_length=255,
        description="Author display name",
        alias="displayName",
        validation_alias=AliasChoices("displayName", "display_name"),
        serialization_alias="displayName",
    )
    email: EmailStr = Field(..., description="Author email address")
    photo_url: Optional[str] = Field(
        None,
        description="Author profile photo URL",
        alias="photoURL",
        validation_alias=AliasChoices("photoURL", "photo_url"),
        serialization_alias="photoURL",
    )
    bio: Optional[str] = Field(None, description="Author biography")
    website: Optional[str] = Field(None, description="Author website URL")
    is_verified: bool = Field(
        default=False,
        description="Author verification status",
        alias="isVerified",
        validation_alias=AliasChoices("isVerified", "is_verified"),
        serialization_alias="isVerified",
    )
    total_books_published: int = Field(
        default=0,
        ge=0,
        description="Total number of books published",
        alias="totalBooksPublished",
        validation_alias=AliasChoices("totalBooksPublished", "total_books_published"),
        serialization_alias="totalBooksPublished",
    )
    average_rating: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Average rating of author's books",
        alias="averageRating",
        validation_alias=AliasChoices("averageRating", "average_rating"),
        serialization_alias="averageRating",
    )
    created_at: datetime = Field(
        ...,
        description="Author account creation timestamp",
        alias="createdAt",
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )

    class Config:
        """Allow population by field name."""

        populate_by_name = True
        from_attributes = True


class AuthorStatistics(BaseModel):
    """Author-specific statistics."""

    total_books_published: int = Field(
        default=0,
        ge=0,
        description="Total number of books published",
        alias="totalBooksPublished",
        validation_alias=AliasChoices("totalBooksPublished", "total_books_published"),
        serialization_alias="totalBooksPublished",
    )
    total_readers_reached: int = Field(
        default=0,
        ge=0,
        description="Total number of readers reached",
        alias="totalReadersReached",
        validation_alias=AliasChoices("totalReadersReached", "total_readers_reached"),
        serialization_alias="totalReadersReached",
    )
    average_rating: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Average rating of author's books",
        alias="averageRating",
        validation_alias=AliasChoices("averageRating", "average_rating"),
        serialization_alias="averageRating",
    )
    total_reviews: int = Field(
        default=0,
        ge=0,
        description="Total number of reviews received",
        alias="totalReviews",
        validation_alias=AliasChoices("totalReviews", "total_reviews"),
        serialization_alias="totalReviews",
    )
    total_followers: int = Field(
        default=0,
        ge=0,
        description="Total number of followers",
        alias="totalFollowers",
        validation_alias=AliasChoices("totalFollowers", "total_followers"),
        serialization_alias="totalFollowers",
    )

    class Config:
        """Allow population by field name."""

        populate_by_name = True


__all__ = [
    "AuthorSocialLinks",
    "AuthorPreferences",
    "AuthorBase",
    "AuthorCreate",
    "AuthorUpdate",
    "Author",
    "AuthorProfile",
    "AuthorStatistics",
]
