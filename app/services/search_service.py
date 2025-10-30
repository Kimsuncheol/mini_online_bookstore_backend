"""
Search Service

Provides comprehensive book search functionality with:
- N-gram based fuzzy matching for typo tolerance
- Content-based filtering
- Search history management
- AI-based keyword suggestions (integrated in Mission 3)

Storage Structure:
- books collection (primary search data)
- books/{book_id}/search_metadata (search-related metadata)
- search_history/{user_id}/queries (search history records)
"""

import time
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot

from app.models.search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchHistoryItem,
    SearchHistoryCreate,
    SearchSettings,
    FuzzySearchMatch,
    SearchAnalytics,
)
from app.models.book import Book
from app.services.book_service import get_book_service
from app.services.search_suggestion_service import get_search_suggestion_service
from app.utils.firebase_config import get_firestore_client
from app.utils.ngram import (
    generate_character_ngrams,
    generate_word_ngrams,
    calculate_string_similarity,
    build_search_index,
    search_using_index,
)


class SearchService:
    """Service class for book search operations."""

    # Collection paths
    BOOKS_COLLECTION = "books"
    SEARCH_HISTORY_COLLECTION = "search_history"
    SEARCH_ANALYTICS_COLLECTION = "search_analytics"

    def __init__(self):
        """Initialize the search service."""
        self.db: Any = get_firestore_client()
        self.book_service = get_book_service()
        self.suggestion_service = get_search_suggestion_service()

        # N-gram configuration
        self.character_ngram_size = 3
        self.word_ngram_size = 2
        self.fuzzy_threshold = 0.6

    # ==================== SEARCH OPERATIONS ====================

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Perform comprehensive book search.

        Combines exact matches, fuzzy matching, and ranking by relevance.

        Args:
            request: Search request with query and filters

        Returns:
            SearchResponse with results and metadata
        """
        start_time = time.time()

        try:
            # Normalize query
            query = request.query.strip()

            if not query:
                return SearchResponse(
                    success=False,
                    error="Search query cannot be empty",
                    processing_time_ms=0,
                )

            # Fetch all books (in production, this might be optimized)
            all_books = self.book_service.get_all_books(limit=None)

            # Perform search based on search type
            results = []
            if request.search_type == "books" or request.search_type == "all":
                results.extend(self._search_books(query, all_books, request.filters))

            if request.search_type == "authors" or request.search_type == "all":
                results.extend(self._search_authors(query, all_books))

            if request.search_type == "categories" or request.search_type == "all":
                results.extend(self._search_categories(query, all_books))

            # Sort results by relevance score
            results.sort(key=lambda x: x.relevance_score or 0, reverse=True)

            # Calculate total count before pagination
            total_count = len(results)

            # Apply pagination
            start_idx = (request.page - 1) * request.page_size
            end_idx = start_idx + request.page_size
            paginated_results = results[start_idx:end_idx]

            # Get AI suggestions if enabled
            suggested_keywords = []
            if request.settings and request.settings.include_suggestions:
                suggested_keywords = await self._get_suggested_keywords(
                    query, paginated_results
                )

            processing_time = int((time.time() - start_time) * 1000)

            # Save search history if enabled
            if request.settings and request.settings.history_enabled:
                await self._save_search_history(
                    query=query,
                    user_id=request.user_id,
                    result_count=total_count,
                    search_type=request.search_type,
                )

            # Save analytics
            await self._save_search_analytics(
                query=query,
                result_count=total_count,
                processing_time_ms=processing_time,
                user_id=request.user_id,
                search_type=request.search_type,
                had_results=total_count > 0,
            )

            return SearchResponse(
                success=True,
                results=paginated_results,
                total_count=total_count,
                suggested_keywords=suggested_keywords[:5],  # Top 5 suggestions
                processing_time_ms=processing_time,
                page=request.page,
                page_size=request.page_size,
                has_more=(start_idx + request.page_size) < total_count,
            )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            return SearchResponse(
                success=False,
                error=f"Search error: {str(e)}",
                processing_time_ms=processing_time,
            )

    # ==================== BOOK SEARCH ====================

    def _search_books(
        self,
        query: str,
        books: List[Book],
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search for books using fuzzy matching and filters.

        Args:
            query: Search query
            books: List of books to search in
            filters: Optional filters (genre, price range, etc.)

        Returns:
            List of matching books as SearchResult
        """
        results = []

        for book in books:
            # Check filters first
            if filters:
                if not self._matches_filters(book, filters):
                    continue

            # Calculate relevance score using fuzzy matching
            title_score = calculate_string_similarity(
                query,
                book.title,
                ngram_type="char",
                n=self.character_ngram_size,
            )
            author_score = calculate_string_similarity(
                query,
                book.author,
                ngram_type="char",
                n=self.character_ngram_size,
            )

            # Use higher of title or author match
            relevance_score = max(title_score, author_score)

            # Boost score if it's a featured book
            if book.is_featured:
                relevance_score = min(relevance_score + 0.1, 1.0)

            # Only include if it meets the threshold
            if relevance_score >= self.fuzzy_threshold:
                results.append(
                    SearchResult(
                        id=book.id,
                        title=book.title,
                        type="book",
                        subtitle=book.author,
                        image_url=book.cover_image_url,
                        url=f"/books/{book.id}",
                        relevance_score=round(relevance_score, 3),
                        description=book.description,
                        metadata={
                            "author": book.author,
                            "genre": book.genre,
                            "price": book.price,
                            "rating": book.rating,
                            "in_stock": book.in_stock,
                        },
                    )
                )

        return results

    def _search_authors(self, query: str, books: List[Book]) -> List[SearchResult]:
        """
        Search for unique authors matching the query.

        Args:
            query: Search query
            books: List of books to extract authors from

        Returns:
            List of matching authors as SearchResult
        """
        results = []
        seen_authors = {}

        for book in books:
            # Calculate relevance score for author
            author_score = calculate_string_similarity(
                query,
                book.author,
                ngram_type="char",
                n=self.character_ngram_size,
            )

            if author_score >= self.fuzzy_threshold:
                if book.author not in seen_authors:
                    seen_authors[book.author] = author_score
                else:
                    # Keep the higher score
                    seen_authors[book.author] = max(seen_authors[book.author], author_score)

        # Convert to SearchResult
        for author, score in seen_authors.items():
            results.append(
                SearchResult(
                    id=f"author_{author.lower().replace(' ', '_')}",
                    title=author,
                    type="author",
                    url=f"/authors/{author.lower().replace(' ', '_')}",
                    relevance_score=round(score, 3),
                    metadata={"author_name": author},
                )
            )

        return results

    def _search_categories(self, query: str, books: List[Book]) -> List[SearchResult]:
        """
        Search for unique categories matching the query.

        Args:
            query: Search query
            books: List of books to extract categories from

        Returns:
            List of matching categories as SearchResult
        """
        results = []
        seen_categories = {}

        for book in books:
            # Calculate relevance score for genre
            genre_score = calculate_string_similarity(
                query,
                book.genre,
                ngram_type="word",
                n=self.word_ngram_size,
            )

            if genre_score >= self.fuzzy_threshold:
                if book.genre not in seen_categories:
                    seen_categories[book.genre] = genre_score
                else:
                    seen_categories[book.genre] = max(seen_categories[book.genre], genre_score)

        # Convert to SearchResult
        for category, score in seen_categories.items():
            results.append(
                SearchResult(
                    id=f"category_{category.lower().replace(' ', '_')}",
                    title=category,
                    type="category",
                    url=f"/categories/{category.lower().replace(' ', '_')}",
                    relevance_score=round(score, 3),
                    metadata={"category_name": category},
                )
            )

        return results

    # ==================== FILTERS ====================

    def _matches_filters(self, book: Book, filters: Dict[str, Any]) -> bool:
        """
        Check if a book matches the provided filters.

        Args:
            book: Book to check
            filters: Filter criteria

        Returns:
            True if book matches all filters
        """
        # Genre filter
        if "genres" in filters and filters["genres"]:
            if book.genre not in filters["genres"]:
                return False

        # Price range filter
        if "min_price" in filters and filters["min_price"] is not None:
            if book.price < filters["min_price"]:
                return False

        if "max_price" in filters and filters["max_price"] is not None:
            if book.price > filters["max_price"]:
                return False

        # Rating filter
        if "rating" in filters and filters["rating"] is not None:
            if book.rating is None or book.rating < filters["rating"]:
                return False

        # Stock filter
        if "in_stock_only" in filters and filters["in_stock_only"]:
            if not book.in_stock:
                return False

        return True

    # ==================== SEARCH HISTORY ====================

    async def _save_search_history(
        self,
        query: str,
        user_id: Optional[str],
        result_count: int,
        search_type: str = "all",
    ) -> None:
        """
        Save search query to history.

        Args:
            query: Search query
            user_id: User ID (optional)
            result_count: Number of results found
            search_type: Type of search performed
        """
        try:
            if not user_id:
                user_id = "anonymous"

            history_item = SearchHistoryCreate(
                query=query,
                user_id=user_id,
                result_count=result_count,
                search_type=search_type,
            )

            # Save to Firestore
            history_ref = (
                self.db.collection(self.SEARCH_HISTORY_COLLECTION)
                .document(user_id)
                .collection("queries")
                .document()
            )
            history_ref.set(history_item.model_dump() | {"timestamp": datetime.now()})

        except Exception as e:
            print(f"Warning: Failed to save search history: {str(e)}")

    def get_search_history(
        self,
        user_id: str,
        limit: int = 20,
    ) -> List[SearchHistoryItem]:
        """
        Retrieve search history for a user.

        Args:
            user_id: User ID
            limit: Maximum number of records to return

        Returns:
            List of search history items
        """
        try:
            docs = (
                self.db.collection(self.SEARCH_HISTORY_COLLECTION)
                .document(user_id)
                .collection("queries")
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
                .stream()
            )

            history = []
            for doc in docs:
                data = doc.to_dict()
                history.append(
                    SearchHistoryItem(
                        id=doc.id,
                        query=data.get("query", ""),
                        timestamp=data.get("timestamp", datetime.now()),
                        user_id=user_id,
                        result_count=data.get("result_count", 0),
                        search_type=data.get("search_type", "all"),
                    )
                )

            return history

        except Exception as e:
            print(f"Warning: Failed to retrieve search history: {str(e)}")
            return []

    # ==================== SEARCH ANALYTICS ====================

    async def _save_search_analytics(
        self,
        query: str,
        result_count: int,
        processing_time_ms: int,
        user_id: Optional[str],
        search_type: str,
        had_results: bool,
    ) -> None:
        """
        Save search analytics for monitoring and optimization.

        Args:
            query: Search query
            result_count: Number of results found
            processing_time_ms: Processing time in milliseconds
            user_id: User ID (optional)
            search_type: Type of search
            had_results: Whether search returned results
        """
        try:
            analytics = SearchAnalytics(
                id=self.db.collection("_temp").document().id,
                query=query,
                result_count=result_count,
                processing_time_ms=processing_time_ms,
                user_id=user_id,
                search_type=search_type,
                had_results=had_results,
                timestamp=datetime.now(),
            )

            self.db.collection(self.SEARCH_ANALYTICS_COLLECTION).document(
                analytics.id
            ).set(analytics.model_dump())

        except Exception as e:
            print(f"Warning: Failed to save search analytics: {str(e)}")

    # ==================== AI SUGGESTIONS (MISSION 3) ====================

    async def _get_suggested_keywords(
        self,
        query: str,
        results: List[SearchResult],
    ) -> List[str]:
        """
        Get AI-based keyword suggestions for search refinement.

        Uses LangChain with content-based filtering to generate intelligent suggestions.
        Integrated from SearchSuggestionService.

        Args:
            query: Original search query
            results: Search results returned

        Returns:
            List of suggested keywords
        """
        try:
            suggestions = await self.suggestion_service.generate_search_suggestions(
                query=query,
                results=results,
                max_suggestions=5,
                use_cache=True,
            )

            return suggestions

        except Exception as e:
            print(f"Warning: Error getting AI suggestions: {str(e)}")
            # Fallback suggestions if AI service fails
            if not results:
                return [
                    f"Try broader search terms",
                    f"Search by author",
                    f"Browse by category",
                ]
            return []

    # ==================== UTILITY METHODS ====================

    def clear_search_history(self, user_id: str) -> bool:
        """
        Clear all search history for a user.

        Args:
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        try:
            docs = (
                self.db.collection(self.SEARCH_HISTORY_COLLECTION)
                .document(user_id)
                .collection("queries")
                .stream()
            )

            for doc in docs:
                doc.reference.delete()

            return True

        except Exception as e:
            print(f"Warning: Failed to clear search history: {str(e)}")
            return False

    def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most popular search queries across all users.

        Args:
            limit: Maximum number of searches to return

        Returns:
            List of popular searches with counts
        """
        try:
            # This is a simplified implementation
            # In production, consider using aggregation pipelines
            docs = (
                self.db.collection(self.SEARCH_ANALYTICS_COLLECTION)
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit * 5)
                .stream()
            )

            query_counts: Dict[str, int] = {}
            for doc in docs:
                data = doc.to_dict()
                query = data.get("query", "")
                if query:
                    query_counts[query] = query_counts.get(query, 0) + 1

            # Sort by count
            sorted_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)

            return [
                {"query": query, "count": count}
                for query, count in sorted_queries[:limit]
            ]

        except Exception as e:
            print(f"Warning: Failed to get popular searches: {str(e)}")
            return []


# Convenience function to create a service instance
def get_search_service() -> SearchService:
    """Create and return a search service instance."""
    return SearchService()
