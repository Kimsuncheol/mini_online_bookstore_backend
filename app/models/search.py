"""
Search Models

Defines Pydantic models for search functionality.
Aligned with client-side Search interfaces from the Next.js application.

Data storage: 'books' collection with search metadata
"""

from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


def to_camel(string: str) -> str:
    """Convert snake_case strings to camelCase for JSON serialization."""
    parts = string.split("_")
    if not parts:
        return string
    return parts[0] + "".join(word.capitalize() or "_" for word in parts[1:])


# ==================== SEARCH HISTORY ====================


class SearchHistoryItem(BaseModel):
    """
    Search history item model.

    Represents a record of a search query performed by a user.
    Aligned with client-side SearchHistoryItem interface from Next.js.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    id: str = Field(..., description="Unique search history item identifier")
    query: str = Field(..., min_length=1, max_length=500, description="The search query performed")
    timestamp: int = Field(..., description="When the search was performed (Unix timestamp in milliseconds)")
    user_email: Optional[str] = Field(None, description="Email of the user who performed the search")
    search_type: Optional[str] = Field(None, description="Type of search performed (all, books, authors, categories)")
    result_count: Optional[int] = Field(None, ge=0, description="Number of results found")


class SearchHistoryCreate(BaseModel):
    """Model for creating new search history items."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    query: str = Field(..., min_length=1, max_length=500, description="The search query")
    timestamp: int = Field(..., description="When the search was performed (Unix timestamp in milliseconds)")
    user_email: Optional[str] = Field(None, description="Email of the user who performed the search")
    search_type: Optional[str] = Field(None, description="Type of search performed")
    result_count: Optional[int] = Field(None, ge=0, description="Number of results found")


# ==================== SEARCH RESULTS ====================


class SearchResult(BaseModel):
    """
    Search result model.

    Represents a single result from a search operation.
    Can be a book, author, or category.
    Aligned with client-side SearchResult interface from Next.js.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    id: str = Field(..., description="Unique result identifier")
    title: str = Field(..., min_length=1, description="Result title")
    type: Literal["book", "author", "category"] = Field(
        ..., description="Type of search result"
    )
    subtitle: Optional[str] = Field(None, description="Subtitle or secondary title")
    description: Optional[str] = Field(None, description="Description of the result")
    image: Optional[str] = Field(None, description="Image URL for the result (renamed from image_url)")
    url: Optional[str] = Field(None, description="URL/path to access the result")
    score: Optional[float] = Field(None, ge=0, le=1, description="Relevance score (renamed from relevance_score)")


class SearchResultCollection(BaseModel):
    """Collection of search results with metadata."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    results: List[SearchResult] = Field(
        default_factory=list, description="List of search results"
    )
    total_count: int = Field(
        default=0, ge=0, description="Total number of results found"
    )
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")


# ==================== SEARCH SETTINGS ====================


class SearchSettings(BaseModel):
    """
    Search settings model.

    Configuration for search functionality behavior.
    Aligned with client-side SearchSettings interface from Next.js.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    history_enabled: bool = Field(
        default=True, description="Whether to save search history"
    )


# ==================== SEARCH REQUESTS ====================


class SearchRequest(BaseModel):
    """
    Search request model.

    Used for initiating a search operation.
    Aligned with client-side SearchRequest interface from Next.js.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    query: str = Field(
        ..., min_length=1, max_length=500,
        description="Search query string"
    )
    search_type: Optional[Literal["all", "books", "authors", "categories"]] = Field(
        default="all", description="Type of search to perform"
    )
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")
    user_email: Optional[str] = Field(None, description="User email for personalized search")


class SearchRequestInternal(SearchRequest):
    """
    Extended search request model for internal use.

    Includes additional fields like filters and settings that are not exposed in the public API.
    """

    filters: Optional[Dict[str, Any]] = Field(
        None, description="Additional search filters (genre, price range, etc.)"
    )
    settings: Optional[SearchSettings] = Field(
        None, description="Search settings configuration"
    )


# ==================== SEARCH RESPONSES ====================


class SearchResponse(BaseModel):
    """
    Search response model.

    Complete response from a search operation.
    Aligned with client-side SearchResponse interface from Next.js.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    query: str = Field(..., description="The search query that was executed")
    results: List[SearchResult] = Field(
        default_factory=list, description="List of search results"
    )
    suggestions: Optional[List[str]] = Field(
        None, description="AI-suggested keywords or search refinements"
    )
    total: int = Field(
        default=0, ge=0, description="Total number of results found"
    )
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")
    has_more: bool = Field(default=False, description="Whether there are more results available")


# ==================== FUZZY SEARCH ====================


class FuzzySearchMatch(BaseModel):
    """
    Fuzzy search match result.

    Represents a fuzzy match result with similarity score.
    Used internally by the search service.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    item_id: str = Field(..., description="ID of the matched item")
    item_title: str = Field(..., description="Title of the matched item")
    similarity_score: float = Field(
        ..., ge=0, le=1,
        description="Similarity score between query and item (0-1)"
    )
    match_type: Literal["title", "author", "description", "keywords"] = Field(
        default="title", description="Which field matched"
    )


# ==================== SEARCH ANALYTICS ====================


class SearchAnalytics(BaseModel):
    """
    Search analytics model.

    Tracks search statistics and patterns for analytics.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    id: str = Field(..., description="Unique analytics record ID")
    query: str = Field(..., description="The search query")
    result_count: int = Field(default=0, ge=0, description="Number of results found")
    processing_time_ms: int = Field(default=0, ge=0, description="Processing time in milliseconds")
    user_email: Optional[str] = Field(None, description="Email of user who performed search")
    search_type: Literal["all", "books", "authors", "categories"] = Field(
        default="all", description="Type of search"
    )
    had_results: bool = Field(default=False, description="Whether search returned results")
    timestamp: datetime = Field(..., description="When the search was performed")
    filters_used: Optional[Dict[str, Any]] = Field(None, description="Filters applied to search")
