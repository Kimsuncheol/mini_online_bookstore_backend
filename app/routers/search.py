"""
Search Router

API endpoints for book search functionality.
Integrates SearchService with n-gram fuzzy matching and AI-based suggestions.

Endpoints:
- POST /search: Perform a book search
- GET /search/history/{user_id}: Get search history
- DELETE /search/history/{user_id}: Clear search history
- GET /search/popular: Get popular searches
- GET /search/suggestions/related/{book_id}: Get related searches
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.models.search import (
    SearchRequest,
    SearchResponse,
    SearchHistoryItem,
)
from app.services.search_service import get_search_service
from app.services.search_suggestion_service import get_search_suggestion_service
from app.services.book_service import get_book_service


router = APIRouter(prefix="/api/search", tags=["search"])

search_service = get_search_service()
suggestion_service = get_search_suggestion_service()
book_service = get_book_service()


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Perform a book search with fuzzy matching and AI suggestions.

    Combines n-gram based fuzzy matching with LangChain-powered suggestions.

    Query Parameters:
    - query: Search query (required)
    - search_type: Type of search ('all', 'books', 'authors', 'categories')
    - page: Page number (default: 1)
    - page_size: Results per page (default: 20)
    - user_id: User ID for personalization (optional)

    Returns:
        SearchResponse with results, suggestions, and metadata
    """
    try:
        response = await search_service.search(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/history/{user_id}", response_model=List[SearchHistoryItem])
def get_search_history(
    user_id: str,
    limit: Optional[int] = Query(20, ge=1, le=100),
) -> List[SearchHistoryItem]:
    """
    Get search history for a user.

    Args:
        user_id: User ID
        limit: Maximum number of history items to return

    Returns:
        List of search history items
    """
    try:
        history = search_service.get_search_history(user_id, limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@router.delete("/history/{user_id}")
def clear_search_history(user_id: str) -> dict:
    """
    Clear search history for a user.

    Args:
        user_id: User ID

    Returns:
        Status message
    """
    try:
        success = search_service.clear_search_history(user_id)
        if success:
            return {"message": "Search history cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear search history")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")


@router.get("/popular")
def get_popular_searches(
    limit: Optional[int] = Query(10, ge=1, le=50),
) -> dict:
    """
    Get the most popular search queries.

    Args:
        limit: Maximum number of popular searches to return

    Returns:
        List of popular searches with query counts
    """
    try:
        popular = search_service.get_popular_searches(limit)
        return {
            "popular_searches": popular,
            "total": len(popular),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving popular searches: {str(e)}")


@router.get("/suggestions/related/{book_id}")
async def get_related_searches(book_id: str) -> dict:
    """
    Get search suggestions related to a specific book.

    Uses content-based filtering to find related topics.

    Args:
        book_id: Book ID

    Returns:
        List of related search suggestions
    """
    try:
        book = book_service.get_book_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        suggestions = await suggestion_service.get_related_searches(book, max_suggestions=5)

        return {
            "book_id": book_id,
            "book_title": book.title,
            "related_searches": suggestions,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving suggestions: {str(e)}")


@router.post("/expand")
async def expand_search_query(query: str) -> dict:
    """
    Expand a search query with related terms and synonyms.

    Uses LangChain to generate query variations.

    Args:
        query: Search query to expand

    Returns:
        Dictionary with expanded terms
    """
    try:
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        expanded = await suggestion_service.expand_query(query)

        return {
            "original_query": query,
            "expanded_terms": expanded,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error expanding query: {str(e)}")


@router.post("/analyze-similarity")
async def analyze_content_similarity(
    query: str,
    limit: Optional[int] = Query(5, ge=1, le=20),
) -> dict:
    """
    Analyze content similarity between query and books.

    Uses LangChain for semantic comparison.

    Args:
        query: Search query
        limit: Maximum number of results to return

    Returns:
        Books ranked by semantic similarity
    """
    try:
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        all_books = book_service.get_all_books(limit=20)
        similarity_results = await suggestion_service.analyze_content_similarity(
            query, all_books, top_k=limit
        )

        return {
            "query": query,
            "similar_books": similarity_results,
            "count": len(similarity_results),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing similarity: {str(e)}")
