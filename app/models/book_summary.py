"""
Book Summary Models

Defines Pydantic models for AI-generated book summaries.
These summaries are automatically created using LangChain when books are added or updated.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BookSummaryBase(BaseModel):
    """Base model for AI-generated book summaries."""

    book_id: str = Field(..., description="Reference to the book")

    # AI-Generated Summary Content
    short_summary: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Brief 1-2 sentence summary for quick overview"
    )
    detailed_summary: str = Field(
        ...,
        min_length=50,
        description="Detailed paragraph summary of the book"
    )

    # Book Analysis
    key_themes: List[str] = Field(
        default_factory=list,
        description="Main themes and topics covered in the book"
    )
    target_audience: str = Field(
        ...,
        description="Description of who would enjoy this book"
    )
    reading_level: Optional[str] = Field(
        None,
        description="Reading level (e.g., 'Beginner', 'Intermediate', 'Advanced')"
    )

    # Categorization Tags
    mood_tags: Optional[List[str]] = Field(
        default_factory=list,
        description="Mood/feeling tags (e.g., 'uplifting', 'dark', 'humorous')"
    )
    content_warnings: Optional[List[str]] = Field(
        default_factory=list,
        description="Content warnings if applicable"
    )

    # Recommendation Data
    similar_books_tags: Optional[List[str]] = Field(
        default_factory=list,
        description="Tags to help find similar books"
    )
    why_read_this: Optional[str] = Field(
        None,
        description="Compelling reason why someone should read this book"
    )

    # AI Metadata
    ai_confidence_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="AI confidence in the summary quality (0-1)"
    )
    generated_by_model: str = Field(
        default="gpt-4-turbo-preview",
        description="AI model used to generate summary"
    )


class BookSummaryCreate(BookSummaryBase):
    """Model for creating new book summaries."""

    pass


class BookSummaryUpdate(BaseModel):
    """Model for updating existing book summaries."""

    short_summary: Optional[str] = Field(
        None, min_length=10, max_length=500, description="Short summary"
    )
    detailed_summary: Optional[str] = Field(None, min_length=50, description="Detailed summary")
    key_themes: Optional[List[str]] = Field(None, description="Key themes")
    target_audience: Optional[str] = Field(None, description="Target audience")
    reading_level: Optional[str] = Field(None, description="Reading level")
    mood_tags: Optional[List[str]] = Field(None, description="Mood tags")
    content_warnings: Optional[List[str]] = Field(None, description="Content warnings")
    similar_books_tags: Optional[List[str]] = Field(None, description="Similar books tags")
    why_read_this: Optional[str] = Field(None, description="Why read this book")
    ai_confidence_score: Optional[float] = Field(None, ge=0, le=1, description="AI confidence")
    generated_by_model: Optional[str] = Field(None, description="AI model used")


class BookSummary(BookSummaryBase):
    """
    Complete book summary model with metadata.

    Represents an AI-generated summary for a book with analysis,
    themes, and recommendation data.
    """

    id: str = Field(..., description="Unique summary identifier")
    created_at: datetime = Field(..., description="Summary creation timestamp")
    updated_at: datetime = Field(..., description="Summary last update timestamp")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BookWithSummary(BaseModel):
    """
    Extended book model that includes AI-generated summary.

    Used for API responses that include both book data and summary.
    """

    # Book fields (we'll import Book type but define inline for simplicity)
    id: str
    title: str
    author: str
    description: Optional[str]
    genre: str
    price: float
    rating: Optional[float]
    cover_image_url: Optional[str]
    in_stock: bool

    # Summary data
    summary: Optional[BookSummary] = Field(None, description="AI-generated summary")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SummaryGenerationRequest(BaseModel):
    """Request model for generating summaries."""

    book_id: str = Field(..., description="Book ID to generate summary for")
    force_regenerate: bool = Field(
        default=False,
        description="Force regeneration even if summary exists"
    )


class SummaryGenerationResponse(BaseModel):
    """Response model for summary generation."""

    success: bool = Field(..., description="Whether generation was successful")
    summary: Optional[BookSummary] = Field(None, description="Generated summary")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")
