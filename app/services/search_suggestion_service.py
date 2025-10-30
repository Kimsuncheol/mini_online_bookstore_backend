"""
Search Suggestion Service

Provides AI-based keyword suggestions using LangChain and OpenAI.
Implements content-based filtering to recommend search refinements.

Features:
- Generate search suggestions based on query and results
- Content-based filtering for book recommendations
- Smart query expansion and refinement suggestions
- Category and author suggestions based on content analysis
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_text_splitters import CharacterTextSplitter

from app.models.search import SearchResult
from app.models.book import Book
from app.services.book_service import get_book_service
from app.utils.firebase_config import get_firestore_client


load_dotenv()


class SearchSuggestionService:
    """Service for AI-powered search suggestions and keyword recommendations."""

    # Firestore collection for caching suggestions
    SUGGESTIONS_CACHE_COLLECTION = "search_suggestions_cache"

    def __init__(self):
        """Initialize the search suggestion service."""
        self.db: Any = get_firestore_client()
        self.book_service = get_book_service()

        # Initialize LangChain LLM
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("AI_SEARCH_MODEL", "gpt-4-turbo-preview")

        temperature_env = os.getenv("AI_SEARCH_MODEL_TEMPERATURE", "0.3")
        try:
            self.temperature = float(temperature_env)
        except (TypeError, ValueError):
            self.temperature = 0.3

        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            openai_api_key=self.api_key,
        )

        # Text splitter for content analysis
        self.text_splitter = CharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
        )

    # ==================== KEYWORD SUGGESTIONS ====================

    async def generate_search_suggestions(
        self,
        query: str,
        results: List[SearchResult],
        max_suggestions: int = 5,
        use_cache: bool = True,
    ) -> List[str]:
        """
        Generate AI-based search suggestions using LangChain.

        Suggests keywords for search refinement based on the query and results.

        Args:
            query: Original search query
            results: Search results returned
            max_suggestions: Maximum number of suggestions to generate
            use_cache: Whether to use cached suggestions

        Returns:
            List of suggested keywords
        """
        try:
            # Check cache first
            if use_cache:
                cached = self._get_cached_suggestions(query)
                if cached:
                    return cached[:max_suggestions]

            # Generate suggestions based on result content
            suggestions = []

            if not results:
                # No results - suggest broader searches
                suggestions = await self._generate_no_results_suggestions(query)
            else:
                # Generate suggestions based on available results
                suggestions = await self._generate_based_on_results(query, results)

            # Limit and cache
            suggestions = suggestions[:max_suggestions]
            self._cache_suggestions(query, suggestions)

            return suggestions

        except Exception as e:
            print(f"Warning: Error generating search suggestions: {str(e)}")
            return []

    async def _generate_no_results_suggestions(self, query: str) -> List[str]:
        """
        Generate suggestions when search returns no results.

        Args:
            query: Search query

        Returns:
            List of suggested keywords
        """
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a helpful book search assistant. The user's search query returned no results.

Suggest 5 alternative search keywords or queries that might help them find what they're looking for.
These should be related to their original query but slightly broader or using different terminology.

Return only the suggestions, one per line, without numbering or bullets.""",
                    ),
                    ("human", f"Original search query: '{query}'"),
                ]
            )

            chain = prompt | self.llm
            response = await chain.ainvoke({})

            suggestions = [
                s.strip()
                for s in response.content.split("\n")
                if s.strip()
            ]

            return suggestions

        except Exception as e:
            print(f"Warning: Error generating no-results suggestions: {str(e)}")
            return [
                f"Try broader search terms",
                f"Search by author instead",
                f"Browse by category",
            ]

    async def _generate_based_on_results(
        self,
        query: str,
        results: List[SearchResult],
    ) -> List[str]:
        """
        Generate suggestions based on available search results.

        Uses content-based filtering to recommend related searches.

        Args:
            query: Search query
            results: Search results

        Returns:
            List of suggested keywords
        """
        try:
            # Extract metadata from results for content-based analysis
            result_summaries = self._summarize_results(results)

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a helpful book search assistant. Based on the search results provided,
                        suggest 5 related search keywords or topics that users might be interested in.

These suggestions should help users explore similar books or refine their search.
Consider genres, authors, themes, and related topics.

Return only the suggestions, one per line, without numbering or bullets.""",
                    ),
                    (
                        "human",
                        f"""Original search: '{query}'

Search results found:
{result_summaries}

Suggest related search keywords:""",
                    ),
                ]
            )

            chain = prompt | self.llm
            response = await chain.ainvoke({})

            suggestions = [
                s.strip()
                for s in response.content.split("\n")
                if s.strip()
            ]

            return suggestions

        except Exception as e:
            print(f"Warning: Error generating results-based suggestions: {str(e)}")
            return []

    # ==================== CONTENT-BASED FILTERING ====================

    async def get_related_searches(
        self,
        book: Book,
        max_suggestions: int = 5,
    ) -> List[Dict[str, str]]:
        """
        Generate search suggestions related to a specific book.

        Uses content-based filtering to find related topics.

        Args:
            book: Book to generate suggestions for
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested searches with descriptions
        """
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a book recommendation assistant. Given a book's information,
                        suggest 5 related searches or topics that users might be interested in.

Consider the genre, theme, author style, and similar books.
Format each suggestion as: "keyword: description"

Return only the suggestions without numbering.""",
                    ),
                    (
                        "human",
                        f"""Book: {book.title}
Author: {book.author}
Genre: {book.genre}
Description: {book.description or 'No description available'}

Suggest related searches:""",
                    ),
                ]
            )

            chain = prompt | self.llm
            response = await chain.ainvoke({})

            suggestions = []
            for line in response.content.split("\n"):
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        suggestions.append({
                            "keyword": parts[0].strip(),
                            "description": parts[1].strip(),
                        })

            return suggestions[:max_suggestions]

        except Exception as e:
            print(f"Warning: Error generating related searches: {str(e)}")
            return []

    async def analyze_content_similarity(
        self,
        query: str,
        books: List[Book],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Analyze content similarity between query and books.

        Uses LangChain to semantically compare query with book content.

        Args:
            query: Search query
            books: Books to analyze
            top_k: Number of top similar books to return

        Returns:
            List of books with similarity scores
        """
        try:
            if not books:
                return []

            # Prepare book summaries for comparison
            book_summaries = []
            for book in books[:10]:  # Limit to avoid too much processing
                summary = f"""
Title: {book.title}
Author: {book.author}
Genre: {book.genre}
Description: {book.description or 'No description'}
"""
                book_summaries.append({
                    "id": book.id,
                    "summary": summary,
                    "book": book,
                })

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a content analyst. Given a search query and a list of books,
                        analyze the semantic similarity between the query and each book.

For each book, provide a similarity score from 0 to 1.
Return format: "Book Title: 0.85" (one per line)""",
                    ),
                    (
                        "human",
                        f"""Search Query: '{query}'

Books to analyze:
{chr(10).join(s['summary'] for s in book_summaries)}

Provide similarity scores:""",
                    ),
                ]
            )

            chain = prompt | self.llm
            response = await chain.ainvoke({})

            # Parse response
            results = []
            for line in response.content.split("\n"):
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        try:
                            score = float(parts[1].strip())
                            # Find matching book
                            title = parts[0].strip()
                            for book_data in book_summaries:
                                if book_data["book"].title.lower() in title.lower():
                                    results.append({
                                        "book_id": book_data["id"],
                                        "title": book_data["book"].title,
                                        "similarity_score": min(max(score, 0), 1),
                                    })
                                    break
                        except ValueError:
                            pass

            # Sort by similarity score
            results.sort(key=lambda x: x["similarity_score"], reverse=True)

            return results[:top_k]

        except Exception as e:
            print(f"Warning: Error analyzing content similarity: {str(e)}")
            return []

    # ==================== QUERY EXPANSION ====================

    async def expand_query(self, query: str, max_terms: int = 5) -> Dict[str, List[str]]:
        """
        Expand a search query with related terms and synonyms.

        Uses LangChain to generate query variations.

        Args:
            query: Original query
            max_terms: Maximum number of expansion terms

        Returns:
            Dictionary with expanded terms, synonyms, and related terms
        """
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a query expansion assistant. Given a search query,
                        provide related terms, synonyms, and broader/narrower versions.

Return in format:
Synonyms: term1, term2, term3
Related: term1, term2, term3
Broader: term1, term2
Narrower: term1, term2""",
                    ),
                    ("human", f"Query: '{query}'"),
                ]
            )

            chain = prompt | self.llm
            response = await chain.ainvoke({})

            # Parse response
            expanded = {
                "synonyms": [],
                "related": [],
                "broader": [],
                "narrower": [],
            }

            for line in response.content.split("\n"):
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        terms = [t.strip() for t in parts[1].split(",") if t.strip()]

                        if key == "synonyms":
                            expanded["synonyms"] = terms[:max_terms]
                        elif key == "related":
                            expanded["related"] = terms[:max_terms]
                        elif key == "broader":
                            expanded["broader"] = terms[:max_terms]
                        elif key == "narrower":
                            expanded["narrower"] = terms[:max_terms]

            return expanded

        except Exception as e:
            print(f"Warning: Error expanding query: {str(e)}")
            return {
                "synonyms": [],
                "related": [],
                "broader": [],
                "narrower": [],
            }

    # ==================== HELPER METHODS ====================

    def _summarize_results(self, results: List[SearchResult]) -> str:
        """
        Summarize search results for context.

        Args:
            results: Search results

        Returns:
            Formatted summary string
        """
        summary_parts = []

        for result in results[:5]:  # Limit to first 5
            part = f"- {result.title} ({result.type})"
            if result.description:
                part += f": {result.description[:100]}..."
            summary_parts.append(part)

        return "\n".join(summary_parts)

    def _get_cached_suggestions(self, query: str) -> Optional[List[str]]:
        """
        Retrieve cached suggestions for a query.

        Args:
            query: Search query

        Returns:
            Cached suggestions or None
        """
        try:
            doc = self.db.collection(self.SUGGESTIONS_CACHE_COLLECTION).document(
                query.lower().replace(" ", "_")
            ).get()

            if doc.exists:
                data = doc.to_dict()
                # Check if cache is still fresh (24 hours)
                cached_time = data.get("cached_at")
                if cached_time:
                    age = (datetime.now() - cached_time).total_seconds()
                    if age < 86400:  # 24 hours
                        return data.get("suggestions", [])

            return None

        except Exception as e:
            print(f"Warning: Error retrieving cached suggestions: {str(e)}")
            return None

    def _cache_suggestions(self, query: str, suggestions: List[str]) -> None:
        """
        Cache suggestions for a query.

        Args:
            query: Search query
            suggestions: Suggestions to cache
        """
        try:
            self.db.collection(self.SUGGESTIONS_CACHE_COLLECTION).document(
                query.lower().replace(" ", "_")
            ).set({
                "query": query,
                "suggestions": suggestions,
                "cached_at": datetime.now(),
            })

        except Exception as e:
            print(f"Warning: Error caching suggestions: {str(e)}")


# Convenience function to create a service instance
def get_search_suggestion_service() -> SearchSuggestionService:
    """Create and return a search suggestion service instance."""
    return SearchSuggestionService()
