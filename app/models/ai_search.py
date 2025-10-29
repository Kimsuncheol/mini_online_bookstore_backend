"""
AI Search Models

Defines Pydantic models for AI-powered book search functionality.
Aligned with client-side AISearch interfaces from the Next.js application.
"""

from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


def to_camel(string: str) -> str:
    """Convert snake_case strings to camelCase."""
    parts = string.split("_")
    if not parts:
        return string
    return parts[0] + "".join(word.capitalize() or "_" for word in parts[1:])


# ==================== NESTED MODELS ====================


class SearchContext(BaseModel):
    """Search context for AI search questions."""

    previous_question_id: Optional[str] = Field(
        None, description="Reference to previous question in conversation"
    )
    genre: Optional[str] = Field(None, description="Genre filter if specified by user")
    price_range: Optional[Dict[str, Optional[float]]] = Field(
        None, description="Price range filter with min/max values"
    )
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


class ModelConfig(BaseModel):
    """AI model configuration parameters."""

    temperature: Optional[float] = Field(
        0.1, ge=0, le=1, description="Control randomness (0-1)"
    )
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum response length")
    top_p: Optional[float] = Field(None, ge=0, le=1, description="Nucleus sampling parameter")


class RecommendedBook(BaseModel):
    """Recommended book from AI analysis."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    book_id: str = Field(..., description="Book identifier")
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance to question (0-1)")
    reason: str = Field(..., description="Why this book was recommended")
    price: Optional[float] = Field(None, description="Book price")
    original_price: Optional[float] = Field(None, description="Original list price")
    currency: Optional[str] = Field(None, description="Currency code (ISO 4217)")
    description: Optional[str] = Field(None, description="Short synopsis or description")
    genre: Optional[str] = Field(None, description="Primary genre classification")
    language: Optional[str] = Field(None, description="Language of the book")
    isbn: Optional[str] = Field(None, description="ISBN identifier")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    page_count: Optional[int] = Field(None, description="Number of pages")
    publisher: Optional[str] = Field(None, description="Publisher name")
    cover_image_url: Optional[str] = Field(None, description="Cover image URL")
    cover_image: Optional[str] = Field(None, description="Cover image filename")
    pdf_url: Optional[str] = Field(None, description="Public URL to the book PDF")
    pdf_file_name: Optional[str] = Field(
        None, description="Storage path or filename for the book PDF"
    )
    in_stock: Optional[bool] = Field(None, description="Availability status")
    stock_quantity: Optional[int] = Field(None, description="Units in stock")
    rating: Optional[float] = Field(None, description="Average rating")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    is_new: Optional[bool] = Field(None, description="Flag for new releases")
    is_featured: Optional[bool] = Field(None, description="Flag for featured titles")
    discount: Optional[float] = Field(None, description="Discount percentage")
    preview_text: Optional[str] = Field(
        None,
        description="Short excerpt extracted from the book PDF for context",
    )


class ModelMetadata(BaseModel):
    """AI model metadata for responses."""

    model: str = Field(..., description="Model name (e.g., 'gpt-4', 'claude-3')")
    tokens_used: int = Field(..., ge=0, description="Number of tokens consumed")
    confidence: float = Field(..., ge=0, le=1, description="AI confidence in answer (0-1)")
    processing_time: int = Field(..., ge=0, description="Processing time in milliseconds")


class SourceInfo(BaseModel):
    """Source information for AI responses."""

    type: Literal["book", "author", "genre", "knowledge_base"] = Field(
        ..., description="Type of source"
    )
    reference: str = Field(..., description="Reference identifier")
    title: Optional[str] = Field(None, description="Source title")


class AISearchMessage(BaseModel):
    """Single message in an AI search conversation."""

    id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Parent conversation ID")
    role: Literal["user", "assistant"] = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    book_references: Optional[List[str]] = Field(
        None, description="Book IDs mentioned in message"
    )


# ==================== MAIN MODELS ====================


class AISearchQuestionBase(BaseModel):
    """Base model for AI search questions."""

    question: str = Field(..., min_length=1, description="The question to ask")
    user_email: str = Field(..., description="User's email address")
    search_context: Optional[SearchContext] = Field(None, description="Search context")
    ai_model_config: Optional[ModelConfig] = Field(
        None, description="AI model configuration"
    )


class AISearchQuestionCreate(AISearchQuestionBase):
    """Model for creating new AI search questions."""

    pass


class AISearchQuestion(AISearchQuestionBase):
    """Complete AI search question model with metadata."""

    id: str = Field(..., description="Unique question identifier")
    created_at: datetime = Field(..., description="Question creation timestamp")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AISearchAnswerBase(BaseModel):
    """Base model for AI search answers."""

    question_id: str = Field(..., description="Reference to the question")
    answer: str = Field(..., description="AI-generated answer")
    user_email: str = Field(..., description="User's email address")
    recommended_books: Optional[List[RecommendedBook]] = Field(
        None, description="Recommended books from AI analysis"
    )
    suggestions: Optional[List[str]] = Field(
        None, description="Follow-up questions or search refinements"
    )
    model_metadata: Optional[ModelMetadata] = Field(None, description="AI model metadata")
    sources: Optional[List[SourceInfo]] = Field(None, description="Source information")


class AISearchAnswerCreate(AISearchAnswerBase):
    """Model for creating new AI search answers."""

    pass


class AISearchAnswer(AISearchAnswerBase):
    """Complete AI search answer model with metadata."""

    id: str = Field(..., description="Unique answer identifier")
    created_at: datetime = Field(..., description="Answer creation timestamp")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AISearchConversationBase(BaseModel):
    """Base model for AI search conversations."""

    user_email: str = Field(..., description="User's email address")
    title: str = Field(..., description="Conversation title (auto-generated from first question)")


class AISearchConversationCreate(AISearchConversationBase):
    """Model for creating new AI search conversations."""

    pass


class AISearchConversation(AISearchConversationBase):
    """Complete AI search conversation model."""

    id: str = Field(..., description="Unique conversation identifier")
    created_at: datetime = Field(..., description="Conversation creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    messages: List[AISearchMessage] = Field(
        default_factory=list, description="Conversation messages"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AISearchHistory(BaseModel):
    """Simplified model for displaying search history."""

    id: str = Field(..., description="Unique identifier")
    question: str = Field(..., description="The question asked")
    answer: str = Field(..., description="The AI answer")
    user_email: str = Field(..., description="User's email address")
    created_at: datetime = Field(..., description="Creation timestamp")
    book_recommendations: Optional[int] = Field(
        None, description="Count of recommended books"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==================== REQUEST/RESPONSE MODELS ====================


class AISearchRequest(BaseModel):
    """Request model for AI search API."""

    question: str = Field(..., min_length=1, description="The question to ask")
    user_email: str = Field(..., description="User's email address")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID if continuing a conversation"
    )
    context: Optional[Dict[str, Any]] = Field(None, description="Search context")


class AISearchResponseData(BaseModel):
    """Data payload for AI search response."""

    question_id: str = Field(..., description="Created question ID")
    answer_id: str = Field(..., description="Created answer ID")
    answer: str = Field(..., description="AI-generated answer")
    recommended_books: Optional[List[RecommendedBook]] = Field(
        None, description="Recommended books"
    )
    suggestions: Optional[List[str]] = Field(None, description="Follow-up suggestions")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")


class AISearchErrorData(BaseModel):
    """Error data for AI search response."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")


class AISearchResponse(BaseModel):
    """Response model for AI search API."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[AISearchResponseData] = Field(None, description="Response data if successful")
    error: Optional[AISearchErrorData] = Field(None, description="Error data if failed")
