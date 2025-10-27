"""
Like Model

Defines the Pydantic models for user's liked books.
Aligned with the client-side Like interface from Next.js application.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class LikeBase(BaseModel):
    """Base like model with common fields."""

    # Book Information
    book_id: str = Field(..., description="The ID of the liked book")
    title: str = Field(..., min_length=1, max_length=500, description="Book title")

    # User Information
    user_email: str = Field(..., description="User's email address")

    # Pricing Information
    price: float = Field(..., gt=0, description="Current price")
    original_price: Optional[float] = Field(None, gt=0, description="Original price before discount")

    # Media
    cover_image_url: Optional[str] = Field(None, description="Cover image URL")


class LikeCreate(LikeBase):
    """Like model for creating new likes."""

    pass


class Like(LikeBase):
    """
    Complete like model with metadata.

    Represents a user's liked book in the BookNest online bookstore.
    """

    id: str = Field(..., description="Unique like identifier (Firestore document ID)")
    created_at: datetime = Field(..., description="Like creation timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True


class LikeResponse(BaseModel):
    """
    Client-facing like response model.

    Matches the Next.js client interface with camelCase field names.
    """

    book_id: str = Field(..., description="Book ID", alias="bookId")
    title: str = Field(..., description="Book title")
    user_email: str = Field(..., description="User email", alias="userEmail")
    price: float = Field(..., description="Current price")
    original_price: Optional[float] = Field(None, description="Original price", alias="originalPrice")
    cover_image_url: Optional[str] = Field(None, description="Cover image URL", alias="coverImageUrl")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp", alias="createdAt")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True


class LikeStatusResponse(BaseModel):
    """Response model for checking like status."""

    is_liked: bool = Field(..., description="Whether the book is liked by the user")
    like_id: Optional[str] = Field(None, description="Like ID if liked")


class LikeCountResponse(BaseModel):
    """Response model for like count."""

    book_id: str = Field(..., description="Book ID")
    like_count: int = Field(..., ge=0, description="Number of likes for the book")
