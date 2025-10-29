"""
Book Summary Service

Provides AI-powered book summary generation using LangChain and ChatGPT.
Automatically generates summaries, themes, and recommendations for books.
"""

import os
import json
from typing import Optional, Any, List, TYPE_CHECKING
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from app.models.book import Book
from app.models.book_summary import (
    BookSummary,
    BookSummaryCreate,
    BookSummaryUpdate,
)
from app.utils.firebase_config import get_firestore_client

if TYPE_CHECKING:
    from app.services.book_service import BookService


# Pydantic model for structured output parsing
class SummaryOutput(BaseModel):
    """Structured output for AI-generated book summary."""

    short_summary: str = Field(description="Brief 1-2 sentence summary")
    detailed_summary: str = Field(description="Detailed paragraph summary")
    key_themes: List[str] = Field(description="3-5 main themes")
    target_audience: str = Field(description="Who would enjoy this book")
    reading_level: str = Field(description="Reading level: Beginner/Intermediate/Advanced")
    mood_tags: List[str] = Field(description="2-4 mood tags")
    content_warnings: List[str] = Field(description="Content warnings, empty if none")
    similar_books_tags: List[str] = Field(description="3-5 tags for finding similar books")
    why_read_this: str = Field(description="Compelling reason to read this book")
    confidence: float = Field(description="Confidence score 0-1")


class BookSummaryService:
    """Service class for AI-powered book summary operations."""

    SUMMARIES_COLLECTION = "book_summaries"

    def __init__(self, book_service: Optional["BookService"] = None):
        """Initialize the book summary service."""
        self.db: Any = get_firestore_client()
        self._book_service: Optional["BookService"] = book_service

        # Initialize ChatGPT with LangChain
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,  # Low temperature for consistent summaries
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        # Initialize JSON output parser
        self.parser = JsonOutputParser(pydantic_object=SummaryOutput)

    # ==================== SUMMARY CRUD OPERATIONS ====================

    def create_summary(self, summary_data: BookSummaryCreate) -> BookSummary:
        """
        Create a new book summary.

        Args:
            summary_data: The summary data to create

        Returns:
            BookSummary: The created summary with ID

        Raises:
            Exception: If there's an error creating the summary
        """
        try:
            now = datetime.now()
            data = {
                **summary_data.model_dump(exclude_none=True),
                "created_at": now,
                "updated_at": now,
            }

            doc_ref = self.db.collection(self.SUMMARIES_COLLECTION).document()
            doc_ref.set(data)

            return BookSummary(
                id=doc_ref.id,
                created_at=now,
                updated_at=now,
                **summary_data.model_dump(),
            )
        except Exception as e:
            raise Exception(f"Error creating summary: {str(e)}")

    def get_summary_by_book_id(self, book_id: str) -> Optional[BookSummary]:
        """
        Fetch summary for a specific book.

        Args:
            book_id: The book ID

        Returns:
            Optional[BookSummary]: Summary if found, None otherwise
        """
        try:
            docs = (
                self.db.collection(self.SUMMARIES_COLLECTION)
                .where("book_id", "==", book_id)
                .limit(1)
                .stream()
            )

            docs_list = list(docs)
            if docs_list:
                return self._document_to_summary(docs_list[0])
            return None
        except Exception as e:
            raise Exception(f"Error fetching summary: {str(e)}")

    def get_summary_by_id(self, summary_id: str) -> Optional[BookSummary]:
        """
        Fetch a summary by its ID.

        Args:
            summary_id: The summary ID

        Returns:
            Optional[BookSummary]: Summary if found, None otherwise
        """
        try:
            doc = self.db.collection(self.SUMMARIES_COLLECTION).document(summary_id).get()

            if doc.exists:
                return self._document_to_summary(doc)
            return None
        except Exception as e:
            raise Exception(f"Error fetching summary: {str(e)}")

    def update_summary(
        self, summary_id: str, update_data: BookSummaryUpdate
    ) -> Optional[BookSummary]:
        """
        Update an existing summary.

        Args:
            summary_id: The summary ID
            update_data: The data to update

        Returns:
            Optional[BookSummary]: Updated summary or None if not found
        """
        try:
            doc_ref = self.db.collection(self.SUMMARIES_COLLECTION).document(summary_id)

            if not doc_ref.get().exists:
                return None

            update_fields = {
                k: v for k, v in update_data.model_dump().items() if v is not None
            }
            update_fields["updated_at"] = datetime.now()

            doc_ref.update(update_fields)

            return self.get_summary_by_id(summary_id)
        except Exception as e:
            raise Exception(f"Error updating summary: {str(e)}")

    def delete_summary(self, summary_id: str) -> bool:
        """
        Delete a summary.

        Args:
            summary_id: The summary ID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            doc_ref = self.db.collection(self.SUMMARIES_COLLECTION).document(summary_id)

            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            raise Exception(f"Error deleting summary: {str(e)}")

    def delete_summary_by_book_id(self, book_id: str) -> bool:
        """
        Delete summary for a specific book.

        Args:
            book_id: The book ID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            summary = self.get_summary_by_book_id(book_id)
            if summary:
                return self.delete_summary(summary.id)
            return False
        except Exception as e:
            raise Exception(f"Error deleting summary by book ID: {str(e)}")

    # ==================== AI SUMMARY GENERATION ====================

    async def generate_summary_for_book(
        self, book: Book, force_regenerate: bool = False
    ) -> BookSummary:
        """
        Generate AI-powered summary for a book using LangChain.

        Args:
            book: The book to generate summary for
            force_regenerate: Force regeneration even if summary exists

        Returns:
            BookSummary: The generated or existing summary

        Raises:
            Exception: If there's an error generating the summary
        """
        try:
            # Check if summary already exists
            existing_summary = self.get_summary_by_book_id(book.id)
            if existing_summary and not force_regenerate:
                return existing_summary

            # Generate summary using AI
            summary_data = await self._generate_summary_with_ai(book)

            # If summary exists, update it; otherwise create new
            if existing_summary:
                # Update existing summary
                update_data = BookSummaryUpdate(**summary_data.model_dump())
                updated_summary = self.update_summary(existing_summary.id, update_data)
                if updated_summary:
                    return updated_summary

            # Create new summary
            create_data = BookSummaryCreate(
                book_id=book.id,
                **summary_data.model_dump(),
            )
            return self.create_summary(create_data)

        except Exception as e:
            raise Exception(f"Error generating summary for book: {str(e)}")

    def _get_book_service(self) -> Optional["BookService"]:
        """Lazily obtain a book service instance for PDF access."""
        if self._book_service is None:
            try:
                from app.services.book_service import get_book_service
                self._book_service = get_book_service()
            except Exception as exc:
                print(f"Warning: Unable to initialize BookService for summaries: {str(exc)}")
                self._book_service = None
        return self._book_service

    async def _generate_summary_with_ai(self, book: Book) -> SummaryOutput:
        """
        Generate summary using LangChain and ChatGPT.

        Args:
            book: The book to summarize

        Returns:
            SummaryOutput: Structured AI-generated summary
        """
        try:
            # Build system prompt
            system_prompt = """You are an expert book analyst and literary critic.
Your task is to analyze books and create comprehensive, insightful summaries.

You must respond with a valid JSON object matching this exact structure:
{
    "short_summary": "Brief 1-2 sentence summary",
    "detailed_summary": "Detailed paragraph summary (3-5 sentences)",
    "key_themes": ["theme1", "theme2", "theme3"],
    "target_audience": "Description of ideal readers",
    "reading_level": "Beginner/Intermediate/Advanced",
    "mood_tags": ["mood1", "mood2", "mood3"],
    "content_warnings": ["warning1", "warning2"] or [],
    "similar_books_tags": ["tag1", "tag2", "tag3"],
    "why_read_this": "Compelling reason to read",
    "confidence": 0.85
}

Guidelines:
- Keep summaries engaging and informative
- Identify 3-5 key themes
- Be specific about target audience
- Use 2-4 mood tags (e.g., "uplifting", "dark", "humorous", "thought-provoking")
- Include content warnings only if necessary (violence, mature themes, etc.)
- Provide 3-5 tags that would help find similar books
- Write a compelling "why read this" that captures the book's unique value
- Set confidence between 0.7-0.95 based on available information

Return ONLY the JSON object, no additional text."""

            # Build book information prompt
            book_info = f"""
Book Information:
Title: {book.title}
Author: {book.author}
Genre: {book.genre}
Description: {book.description or 'No description available'}
Publisher: {book.publisher or 'Unknown'}
Language: {book.language or 'English'}
Page Count: {book.page_count or 'Unknown'}
"""

            pdf_preview: Optional[str] = None
            book_service = self._get_book_service()
            if book_service:
                try:
                    pdf_preview = book_service.get_pdf_preview_text(
                        book,
                        max_chars=1000,
                        chunk_size=900,
                        chunk_overlap=150,
                    )
                except Exception as preview_error:
                    print(
                        f"Warning: Failed to fetch PDF preview for book {book.id}: {str(preview_error)}"
                    )

            if pdf_preview:
                trimmed_preview = pdf_preview.strip()
                if len(trimmed_preview) > 1000:
                    trimmed_preview = trimmed_preview[:1000].rstrip() + "..."
                book_info += f"\nSample PDF Excerpt:\n{trimmed_preview}"

            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Analyze this book and provide a comprehensive summary:\n{book_info}")
            ]

            # Get AI response
            response = self.llm.invoke(messages)

            # Parse JSON response
            try:
                # Clean the response content
                content = response.content.strip()

                # Remove markdown code blocks if present
                if content.startswith("```json"):
                    content = content[7:]  # Remove ```json
                if content.startswith("```"):
                    content = content[3:]  # Remove ```
                if content.endswith("```"):
                    content = content[:-3]  # Remove trailing ```

                content = content.strip()

                # Parse JSON
                summary_dict = json.loads(content)

                # Create SummaryOutput object
                summary_output = SummaryOutput(
                    short_summary=summary_dict.get("short_summary", ""),
                    detailed_summary=summary_dict.get("detailed_summary", ""),
                    key_themes=summary_dict.get("key_themes", []),
                    target_audience=summary_dict.get("target_audience", "General readers"),
                    reading_level=summary_dict.get("reading_level", "Intermediate"),
                    mood_tags=summary_dict.get("mood_tags", []),
                    content_warnings=summary_dict.get("content_warnings", []),
                    similar_books_tags=summary_dict.get("similar_books_tags", []),
                    why_read_this=summary_dict.get("why_read_this", ""),
                    confidence=summary_dict.get("confidence", 0.8),
                )

                return summary_output

            except json.JSONDecodeError as e:
                # Fallback to basic summary if JSON parsing fails
                print(f"Warning: Failed to parse AI response as JSON: {str(e)}")
                print(f"Response content: {response.content[:200]}")

                # Return a basic summary based on book info
                return SummaryOutput(
                    short_summary=f"{book.title} by {book.author} - A {book.genre} book.",
                    detailed_summary=book.description or f"This {book.genre} book by {book.author} offers readers an engaging experience.",
                    key_themes=[book.genre],
                    target_audience="Readers interested in " + book.genre,
                    reading_level="Intermediate",
                    mood_tags=[book.genre.lower()],
                    content_warnings=[],
                    similar_books_tags=[book.genre, book.author],
                    why_read_this=f"Experience {book.author}'s unique perspective on {book.genre}.",
                    confidence=0.5,
                )

        except Exception as e:
            raise Exception(f"Error generating AI summary: {str(e)}")

    # ==================== BATCH OPERATIONS ====================

    async def generate_summaries_for_all_books(
        self, books: List[Book], skip_existing: bool = True
    ) -> List[BookSummary]:
        """
        Generate summaries for multiple books.

        Args:
            books: List of books to generate summaries for
            skip_existing: Skip books that already have summaries

        Returns:
            List[BookSummary]: List of generated summaries
        """
        summaries = []
        for book in books:
            try:
                # Check if should skip
                if skip_existing:
                    existing = self.get_summary_by_book_id(book.id)
                    if existing:
                        summaries.append(existing)
                        continue

                # Generate summary
                summary = await self.generate_summary_for_book(
                    book, force_regenerate=not skip_existing
                )
                summaries.append(summary)

            except Exception as e:
                print(f"Warning: Failed to generate summary for book {book.id}: {str(e)}")
                continue

        return summaries

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _document_to_summary(doc: DocumentSnapshot) -> BookSummary:
        """Convert Firestore document to BookSummary."""
        data = doc.to_dict()
        return BookSummary(
            id=doc.id,
            book_id=data.get("book_id"),
            short_summary=data.get("short_summary"),
            detailed_summary=data.get("detailed_summary"),
            key_themes=data.get("key_themes", []),
            target_audience=data.get("target_audience"),
            reading_level=data.get("reading_level"),
            mood_tags=data.get("mood_tags", []),
            content_warnings=data.get("content_warnings", []),
            similar_books_tags=data.get("similar_books_tags", []),
            why_read_this=data.get("why_read_this"),
            ai_confidence_score=data.get("ai_confidence_score", 0.8),
            generated_by_model=data.get("generated_by_model", "gpt-4-turbo-preview"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


# Convenience function
def get_book_summary_service() -> BookSummaryService:
    """Create and return a book summary service instance."""
    return BookSummaryService()
