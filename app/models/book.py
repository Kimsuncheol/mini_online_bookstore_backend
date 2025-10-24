"""
Book Model

Defines the Pydantic models for books, categories, reviews, and filter options.
Aligned with the client-side Book interfaces from BookNest application.
"""

from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class BookBase(BaseModel):
    """Base book model with common fields."""

    # Basic Information
    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    author: str = Field(..., min_length=1, max_length=255, description="Book author")
    isbn: Optional[str] = Field(None, max_length=20, description="ISBN number")

    # Description and Content
    description: Optional[str] = Field(None, description="Book description")
    genre: str = Field(..., min_length=1, max_length=100, description="Book genre")
    language: Optional[str] = Field(None, max_length=50, description="Book language")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    page_count: Optional[int] = Field(None, gt=0, description="Number of pages")

    # Pricing and Availability
    price: float = Field(..., gt=0, description="Current price (must be > 0)")
    original_price: Optional[float] = Field(None, gt=0, description="Original price before discount")
    currency: Optional[str] = Field(default="USD", max_length=3, description="Currency code (ISO 4217)")
    in_stock: bool = Field(default=True, description="Stock availability status")
    stock_quantity: int = Field(..., ge=0, description="Available stock quantity")

    # Media
    cover_image: Optional[str] = Field(None, description="Cover image filename")
    cover_image_url: Optional[str] = Field(None, description="Cover image URL")

    # Ratings and Reviews
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating (0-5)")
    review_count: Optional[int] = Field(default=0, ge=0, description="Number of reviews")

    # Publishing Information
    publisher: Optional[str] = Field(None, max_length=255, description="Publisher name")
    edition: Optional[str] = Field(None, max_length=100, description="Book edition")

    # Additional Metadata
    is_new: Optional[bool] = Field(default=False, description="Is this a new release?")
    is_featured: Optional[bool] = Field(default=False, description="Is this a featured book?")
    discount: Optional[float] = Field(None, ge=0, le=100, description="Discount percentage (0-100)")


class BookCreate(BookBase):
    """Book model for creating new books."""

    pass


class BookUpdate(BaseModel):
    """Book model for updating existing books."""

    # Basic Information
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Book title")
    author: Optional[str] = Field(None, min_length=1, max_length=255, description="Book author")
    isbn: Optional[str] = Field(None, max_length=20, description="ISBN number")

    # Description and Content
    description: Optional[str] = Field(None, description="Book description")
    genre: Optional[str] = Field(None, min_length=1, max_length=100, description="Book genre")
    language: Optional[str] = Field(None, max_length=50, description="Book language")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    page_count: Optional[int] = Field(None, gt=0, description="Number of pages")

    # Pricing and Availability
    price: Optional[float] = Field(None, gt=0, description="Current price")
    original_price: Optional[float] = Field(None, gt=0, description="Original price")
    currency: Optional[str] = Field(None, max_length=3, description="Currency code")
    in_stock: Optional[bool] = Field(None, description="Stock availability status")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity")

    # Media
    cover_image: Optional[str] = Field(None, description="Cover image filename")
    cover_image_url: Optional[str] = Field(None, description="Cover image URL")

    # Ratings and Reviews
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    review_count: Optional[int] = Field(None, ge=0, description="Number of reviews")

    # Publishing Information
    publisher: Optional[str] = Field(None, max_length=255, description="Publisher name")
    edition: Optional[str] = Field(None, max_length=100, description="Book edition")

    # Additional Metadata
    is_new: Optional[bool] = Field(None, description="Is new release?")
    is_featured: Optional[bool] = Field(None, description="Is featured?")
    discount: Optional[float] = Field(None, ge=0, le=100, description="Discount percentage")


class Book(BookBase):
    """
    Complete book model with metadata.

    Represents a book in the BookNest online bookstore with all information
    aligned with the client-side Book interface.
    """

    id: str = Field(..., description="Unique book identifier (Firestore document ID)")
    created_at: datetime = Field(..., description="Book creation timestamp")
    updated_at: datetime = Field(..., description="Book last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True


class BookFilterOptions(BaseModel):
    """
    Book filter options for searching and browsing books.

    Used to filter and sort books based on various criteria.
    """

    genres: Optional[List[str]] = Field(None, description="List of genres to filter by")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating filter")
    in_stock_only: Optional[bool] = Field(None, description="Show only in-stock books")
    search_term: Optional[str] = Field(None, description="Search term for title/author")
    sort_by: Optional[
        Literal["price-low-to-high", "price-high-to-low", "newest", "rating", "title"]
    ] = Field(None, description="Sort order")
    page: Optional[int] = Field(default=1, ge=1, description="Page number for pagination")
    limit: Optional[int] = Field(default=20, ge=1, le=100, description="Items per page")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class BookCategoryBase(BaseModel):
    """Base book category model."""

    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    icon: Optional[str] = Field(None, description="Category icon URL or name")
    book_count: Optional[int] = Field(default=0, ge=0, description="Number of books in category")


class BookCategoryCreate(BookCategoryBase):
    """Book category model for creating new categories."""

    pass


class BookCategoryUpdate(BaseModel):
    """Book category model for updating categories."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    icon: Optional[str] = Field(None, description="Category icon")
    book_count: Optional[int] = Field(None, ge=0, description="Book count")


class BookCategory(BookCategoryBase):
    """
    Complete book category model.

    Represents book categories/genres in the bookstore.
    """

    id: str = Field(..., description="Unique category identifier")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True


class BookReviewBase(BaseModel):
    """Base book review model."""

    book_id: str = Field(..., description="ID of the book being reviewed")
    user_id: str = Field(..., description="ID of the user writing the review")
    user_name: str = Field(..., min_length=1, max_length=255, description="Name of the reviewer")
    rating: float = Field(..., ge=0, le=5, description="Review rating (0-5)")
    title: str = Field(..., min_length=1, max_length=200, description="Review title")
    content: str = Field(..., min_length=1, description="Review content")
    helpful: int = Field(default=0, ge=0, description="Number of helpful votes")


class BookReviewCreate(BookReviewBase):
    """Book review model for creating new reviews."""

    pass


class BookReviewUpdate(BaseModel):
    """Book review model for updating reviews."""

    rating: Optional[float] = Field(None, ge=0, le=5, description="Review rating")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Review title")
    content: Optional[str] = Field(None, min_length=1, description="Review content")
    helpful: Optional[int] = Field(None, ge=0, description="Helpful votes")


class BookReview(BookReviewBase):
    """
    Complete book review model.

    Represents a user review for a book.
    """

    id: str = Field(..., description="Unique review identifier")
    created_at: datetime = Field(..., description="Review creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Review last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True
