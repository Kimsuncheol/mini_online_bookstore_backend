"""
Advertisement Model

Defines the Pydantic models for advertisements (hero carousel books).
Aligned with the client-side HeroCarouselBook interface from Next.js application.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AdvertisementBase(BaseModel):
    """Base advertisement model with common fields."""

    # Reference to book
    book_id: str = Field(..., description="ID of the book being advertised")

    # Display Information (from book data)
    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    author: str = Field(..., min_length=1, max_length=255, description="Book author")
    description: str = Field(..., description="Book description")
    price: float = Field(..., gt=0, description="Current price (must be > 0)")

    # Optional Fields
    page_count: Optional[int] = Field(None, gt=0, description="Number of pages")
    original_price: Optional[float] = Field(None, gt=0, description="Original price before discount")
    cover_image_url: Optional[str] = Field(None, description="Cover image URL")

    # Advertisement Metadata
    is_active: bool = Field(default=True, description="Is the advertisement active?")
    display_order: int = Field(default=0, ge=0, description="Display order in carousel (lower = first)")
    start_date: Optional[datetime] = Field(None, description="Advertisement start date")
    end_date: Optional[datetime] = Field(None, description="Advertisement end date")


class AdvertisementCreate(AdvertisementBase):
    """Advertisement model for creating new advertisements."""

    pass


class AdvertisementUpdate(BaseModel):
    """Advertisement model for updating existing advertisements."""

    # Reference to book
    book_id: Optional[str] = Field(None, description="ID of the book being advertised")

    # Display Information
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Book title")
    author: Optional[str] = Field(None, min_length=1, max_length=255, description="Book author")
    description: Optional[str] = Field(None, description="Book description")
    price: Optional[float] = Field(None, gt=0, description="Current price")

    # Optional Fields
    page_count: Optional[int] = Field(None, gt=0, description="Number of pages")
    original_price: Optional[float] = Field(None, gt=0, description="Original price")
    cover_image_url: Optional[str] = Field(None, description="Cover image URL")

    # Advertisement Metadata
    is_active: Optional[bool] = Field(None, description="Is the advertisement active?")
    display_order: Optional[int] = Field(None, ge=0, description="Display order in carousel")
    start_date: Optional[datetime] = Field(None, description="Advertisement start date")
    end_date: Optional[datetime] = Field(None, description="Advertisement end date")


class Advertisement(AdvertisementBase):
    """
    Complete advertisement model with metadata.

    Represents an advertisement (hero carousel book) in the BookNest online bookstore
    aligned with the client-side HeroCarouselBook interface.
    """

    id: str = Field(..., description="Unique advertisement identifier (Firestore document ID)")
    created_at: datetime = Field(..., description="Advertisement creation timestamp")
    updated_at: datetime = Field(..., description="Advertisement last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True


class HeroCarouselBook(BaseModel):
    """
    Client-side hero carousel book model.

    This matches the Next.js client interface and is used for API responses.
    """

    id: str = Field(..., description="Advertisement/Book ID")
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    description: str = Field(..., description="Book description")
    price: float = Field(..., description="Current price")
    page_count: Optional[int] = Field(None, description="Number of pages", alias="pageCount")
    original_price: Optional[float] = Field(None, description="Original price", alias="originalPrice")
    cover_image_url: Optional[str] = Field(None, description="Cover image URL", alias="coverImageUrl")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True
