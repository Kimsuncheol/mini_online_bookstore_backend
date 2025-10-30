"""
Book Service

Provides business logic and database operations for managing books.
Includes CRUD operations, filtering, searching, and sorting functionality.
Now includes AI-powered summary generation using LangChain.
"""

from typing import List, Optional, Any, Dict, Union
from datetime import datetime
from urllib.parse import urlparse, unquote
from google.cloud.firestore import DocumentSnapshot
import logging
from app.models.book import (
    Book,
    BookCreate,
    BookUpdate,
    BookFilterOptions,
    BookCategory,
    BookCategoryCreate,
    BookCategoryUpdate,
    BookReview,
    BookReviewCreate,
    BookReviewUpdate,
)
from app.utils.firebase_config import get_firestore_client
from app.utils.pdf_loader import (
    PDFLoaderError,
    PDFNotFoundError,
    PDFProcessingError,
    download_pdf_from_storage,
    load_pdf_from_storage,
    load_and_split_pdf_from_storage,
)
from langchain_core.documents import Document
import asyncio

logger = logging.getLogger(__name__)


class BookService:
    """Service class for book-related database operations."""

    BOOKS_COLLECTION = "books"
    CATEGORIES_COLLECTION = "categories"
    REVIEWS_COLLECTION = "reviews"
    DEFAULT_PDF_CHUNK_SIZE = 1000
    DEFAULT_PDF_CHUNK_OVERLAP = 200
    DEFAULT_PDF_PREVIEW_CHARS = 2000

    def __init__(self):
        """Initialize the book service with Firestore client."""
        self.db: Any = get_firestore_client()

    # ==================== PDF OPERATIONS ====================

    def download_book_pdf(
        self,
        book_or_id: Union[Book, str],
        *,
        raise_errors: bool = False,
    ) -> Optional[bytes]:
        """
        Download raw PDF bytes for a book from Firebase Storage.

        Args:
            book_or_id: Book instance or book ID
            raise_errors: If True, propagate loader exceptions instead of returning None

        Returns:
            Optional[bytes]: PDF content if available, otherwise None
        """
        book = self._ensure_book_instance(book_or_id)
        if not book:
            return None

        bucket_path = self._resolve_pdf_storage_path(book)
        if not bucket_path:
            return None

        try:
            return download_pdf_from_storage(bucket_path)
        except PDFNotFoundError:
            return None
        except (PDFLoaderError, PDFProcessingError) as exc:
            if raise_errors:
                raise Exception(
                    f"Error downloading PDF for book {book.id}: {str(exc)}"
                ) from exc
            print(f"Warning: Error downloading PDF for book {book.id}: {str(exc)}")
            return None

    def load_book_pdf_documents(
        self,
        book_or_id: Union[Book, str],
        *,
        raise_errors: bool = False,
    ) -> List[Document]:
        """
        Load PDF pages as LangChain Document objects without splitting.

        Args:
            book_or_id: Book instance or book ID
            raise_errors: If True, propagate loader exceptions instead of returning []

        Returns:
            List[Document]: List of PDF page documents
        """
        book = self._ensure_book_instance(book_or_id)
        if not book:
            return []

        bucket_path = self._resolve_pdf_storage_path(book)
        if not bucket_path:
            return []

        try:
            return load_pdf_from_storage(bucket_path)
        except PDFNotFoundError:
            return []
        except (PDFLoaderError, PDFProcessingError) as exc:
            if raise_errors:
                raise Exception(
                    f"Error loading PDF for book {book.id}: {str(exc)}"
                ) from exc
            print(f"Warning: Error loading PDF for book {book.id}: {str(exc)}")
            return []

    def load_and_split_book_pdf(
        self,
        book_or_id: Union[Book, str],
        *,
        chunk_size: int = DEFAULT_PDF_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_PDF_CHUNK_OVERLAP,
        raise_errors: bool = False,
    ) -> List[Document]:
        """
        Load and split a book PDF into LangChain Documents for downstream processing.

        Args:
            book_or_id: Book instance or book ID
            chunk_size: Target chunk size for splitting
            chunk_overlap: Number of overlapping characters between chunks
            raise_errors: If True, propagate loader exceptions instead of returning []

        Returns:
            List[Document]: Chunked PDF documents
        """
        book = self._ensure_book_instance(book_or_id)
        if not book:
            return []

        bucket_path = self._resolve_pdf_storage_path(book)
        if not bucket_path:
            return []

        try:
            return load_and_split_pdf_from_storage(
                bucket_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        except PDFNotFoundError:
            return []
        except (PDFLoaderError, PDFProcessingError) as exc:
            if raise_errors:
                raise Exception(
                    f"Error loading and splitting PDF for book {book.id}: {str(exc)}"
                ) from exc
            print(f"Warning: Error loading and splitting PDF for book {book.id}: {str(exc)}")
            return []

    def get_pdf_preview_text(
        self,
        book_or_id: Union[Book, str],
        *,
        max_chars: int = DEFAULT_PDF_PREVIEW_CHARS,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> Optional[str]:
        """
        Get a short textual preview extracted from the book PDF.

        Args:
            book_or_id: Book instance or book ID
            max_chars: Maximum number of characters to include in the preview
            chunk_size: Chunk size to use when splitting the PDF
            chunk_overlap: Chunk overlap used when splitting the PDF

        Returns:
            Optional[str]: Preview text or None if unavailable
        """
        chunks = self.load_and_split_book_pdf(
            book_or_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        if not chunks:
            return None

        preview_parts: List[str] = []
        remaining = max_chars

        for chunk in chunks:
            text = (chunk.page_content or "").strip()
            if not text:
                continue

            if len(text) > remaining:
                preview_parts.append(text[:remaining])
                remaining = 0
            else:
                preview_parts.append(text)
                remaining -= len(text)

            if remaining <= 0:
                break

        preview_text = "\n\n".join(part.strip() for part in preview_parts if part.strip())
        return preview_text or None

    # ==================== BOOK CRUD OPERATIONS ====================

    async def create_book(self, book_data: BookCreate, generate_summary: bool = True) -> Book:
        """
        Create a new book in the bookstore.
        Automatically generates AI-powered summary if enabled.

        Args:
            book_data (BookCreate): The book data to create
            generate_summary (bool): Whether to generate AI summary (default: True)

        Returns:
            Book: The created book object with ID

        Raises:
            Exception: If there's an error creating the book
        """
        try:
            logger.info("Received book creation payload: %s", book_data.model_dump())
            now = datetime.now()
            data = {
                **book_data.model_dump(),
                "created_at": now,
                "updated_at": now,
            }
            # Convert datetime fields to Firestore timestamps if present
            if data.get("published_date"):
                data["published_date"] = data["published_date"]

            doc_ref = self.db.collection(self.BOOKS_COLLECTION).document()
            doc_ref.set(data)

            created_book = Book(
                id=doc_ref.id,
                created_at=now,
                updated_at=now,
                **book_data.model_dump(),
            )

            # Generate AI summary asynchronously if enabled
            if generate_summary:
                try:
                    from app.services.book_summary_service import get_book_summary_service
                    summary_service = get_book_summary_service()
                    await summary_service.generate_summary_for_book(created_book)
                    print(f"✓ AI summary generated for book: {created_book.title}")
                except Exception as e:
                    # Don't fail book creation if summary generation fails
                    print(f"Warning: Failed to generate summary for book {created_book.id}: {str(e)}")

            return created_book
        except Exception as e:
            raise Exception(f"Error creating book: {str(e)}")

    def get_book_by_id(self, book_id: str) -> Optional[Book]:
        """
        Fetch a book by its ID.

        Args:
            book_id (str): The unique identifier of the book

        Returns:
            Optional[Book]: Book object if found, None otherwise

        Raises:
            Exception: If there's an error fetching the book
        """
        try:
            doc = self.db.collection(self.BOOKS_COLLECTION).document(book_id).get()

            if doc.exists:
                return self._document_to_book(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching book with ID {book_id}: {str(e)}")

    def get_all_books(self, limit: Optional[int] = None) -> List[Book]:
        """
        Fetch all books from the bookstore.

        Args:
            limit (Optional[int]): Maximum number of books to return

        Returns:
            List[Book]: List of all book objects

        Raises:
            Exception: If there's an error fetching books
        """
        try:
            query = self.db.collection(self.BOOKS_COLLECTION)

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            books = [self._document_to_book(doc) for doc in docs]
            return books
        except Exception as e:
            raise Exception(f"Error fetching all books: {str(e)}")

    async def update_book(
        self,
        book_id: str,
        update_data: BookUpdate,
        regenerate_summary: bool = None
    ) -> Optional[Book]:
        """
        Update an existing book.
        Automatically regenerates AI summary if key fields are updated.

        Args:
            book_id (str): The ID of the book to update
            update_data (BookUpdate): The data to update
            regenerate_summary (bool): Force regenerate summary.
                                       If None, auto-detects based on updated fields.

        Returns:
            Optional[Book]: The updated book object, or None if book doesn't exist

        Raises:
            Exception: If there's an error updating the book
        """
        try:
            doc_ref = self.db.collection(self.BOOKS_COLLECTION).document(book_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return None

            update_fields = {
                k: v for k, v in update_data.model_dump().items() if v is not None
            }
            update_fields["updated_at"] = datetime.now()

            # Determine if summary should be regenerated
            should_regenerate = regenerate_summary
            if should_regenerate is None:
                # Auto-detect: regenerate if key fields are updated
                key_fields = {"title", "author", "description", "genre"}
                updated_keys = set(update_fields.keys())
                should_regenerate = bool(key_fields & updated_keys)

            doc_ref.update(update_fields)

            # Fetch the updated book
            updated_book = self.get_book_by_id(book_id)

            # Regenerate AI summary if needed
            if should_regenerate and updated_book:
                try:
                    from app.services.book_summary_service import get_book_summary_service
                    summary_service = get_book_summary_service()
                    await summary_service.generate_summary_for_book(
                        updated_book,
                        force_regenerate=True
                    )
                    print(f"✓ AI summary regenerated for book: {updated_book.title}")
                except Exception as e:
                    # Don't fail book update if summary generation fails
                    print(f"Warning: Failed to regenerate summary for book {book_id}: {str(e)}")

            return updated_book
        except Exception as e:
            raise Exception(f"Error updating book with ID {book_id}: {str(e)}")

    def delete_book(self, book_id: str) -> bool:
        """
        Delete a book from the bookstore.
        Also deletes associated AI-generated summary.

        Args:
            book_id (str): The ID of the book to delete

        Returns:
            bool: True if book was deleted, False if book doesn't exist

        Raises:
            Exception: If there's an error deleting the book
        """
        try:
            doc_ref = self.db.collection(self.BOOKS_COLLECTION).document(book_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return False

            # Delete the book
            doc_ref.delete()

            # Delete associated summary if exists
            try:
                from app.services.book_summary_service import get_book_summary_service
                summary_service = get_book_summary_service()
                summary_service.delete_summary_by_book_id(book_id)
                print(f"✓ Associated summary deleted for book {book_id}")
            except Exception as e:
                # Don't fail book deletion if summary deletion fails
                print(f"Warning: Failed to delete summary for book {book_id}: {str(e)}")

            return True
        except Exception as e:
            raise Exception(f"Error deleting book with ID {book_id}: {str(e)}")

    # ==================== BOOK SEARCH AND FILTER ====================

    def search_books(self, filters: BookFilterOptions) -> Dict[str, Any]:
        """
        Search and filter books based on various criteria.

        Args:
            filters (BookFilterOptions): Filter options for the search

        Returns:
            Dict containing:
                - books: List of Book objects matching the criteria
                - total: Total number of matching books
                - page: Current page number
                - limit: Items per page
                - total_pages: Total number of pages

        Raises:
            Exception: If there's an error searching books
        """
        try:
            query = self.db.collection(self.BOOKS_COLLECTION)

            # Apply filters
            if filters.genres and len(filters.genres) > 0:
                query = query.where("genre", "in", filters.genres)

            if filters.in_stock_only:
                query = query.where("in_stock", "==", True)

            # Get all matching documents first
            docs = list(query.stream())

            # Apply additional filtering in Python (Firestore limitations)
            filtered_books = []
            for doc in docs:
                book = self._document_to_book(doc)

                # Price filters
                if filters.min_price is not None and book.price < filters.min_price:
                    continue
                if filters.max_price is not None and book.price > filters.max_price:
                    continue

                # Rating filter
                if filters.rating is not None:
                    if book.rating is None or book.rating < filters.rating:
                        continue

                # Search term filter (title or author)
                if filters.search_term:
                    search_term = filters.search_term.lower()
                    if (
                        search_term not in book.title.lower()
                        and search_term not in book.author.lower()
                    ):
                        continue

                filtered_books.append(book)

            # Apply sorting
            if filters.sort_by:
                filtered_books = self._sort_books(filtered_books, filters.sort_by)

            # Calculate pagination
            total = len(filtered_books)
            page = filters.page or 1
            limit = filters.limit or 20
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit

            # Get paginated results
            paginated_books = filtered_books[start_idx:end_idx]

            return {
                "books": paginated_books,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit,  # Ceiling division
            }
        except Exception as e:
            raise Exception(f"Error searching books: {str(e)}")

    def get_books_by_genre(self, genre: str, limit: Optional[int] = None) -> List[Book]:
        """
        Fetch books by genre.

        Args:
            genre (str): The genre to filter by
            limit (Optional[int]): Maximum number of books to return

        Returns:
            List[Book]: List of books in the specified genre

        Raises:
            Exception: If there's an error fetching books
        """
        try:
            query = self.db.collection(self.BOOKS_COLLECTION).where("genre", "==", genre)

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            books = [self._document_to_book(doc) for doc in docs]
            return books
        except Exception as e:
            raise Exception(f"Error fetching books by genre '{genre}': {str(e)}")

    def get_featured_books(self, limit: Optional[int] = 10) -> List[Book]:
        """
        Fetch featured books.

        Args:
            limit (Optional[int]): Maximum number of books to return

        Returns:
            List[Book]: List of featured books

        Raises:
            Exception: If there's an error fetching books
        """
        try:
            query = self.db.collection(self.BOOKS_COLLECTION).where("is_featured", "==", True)

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            books = [self._document_to_book(doc) for doc in docs]
            return books
        except Exception as e:
            raise Exception(f"Error fetching featured books: {str(e)}")

    def get_new_releases(self, limit: Optional[int] = 10) -> List[Book]:
        """
        Fetch new release books.

        Args:
            limit (Optional[int]): Maximum number of books to return

        Returns:
            List[Book]: List of new release books

        Raises:
            Exception: If there's an error fetching books
        """
        try:
            query = self.db.collection(self.BOOKS_COLLECTION).where("is_new", "==", True)

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            books = [self._document_to_book(doc) for doc in docs]
            return books
        except Exception as e:
            raise Exception(f"Error fetching new releases: {str(e)}")

    async def update_stock(self, book_id: str, quantity_change: int) -> Optional[Book]:
        """
        Update book stock quantity.

        Args:
            book_id (str): The ID of the book
            quantity_change (int): Amount to change (positive or negative)

        Returns:
            Optional[Book]: Updated book object, or None if book doesn't exist

        Raises:
            Exception: If there's an error updating stock
            ValueError: If stock would go negative
        """
        try:
            book = self.get_book_by_id(book_id)
            if not book:
                return None

            new_quantity = book.stock_quantity + quantity_change

            if new_quantity < 0:
                raise ValueError(
                    f"Cannot reduce stock by {abs(quantity_change)}. "
                    f"Current stock: {book.stock_quantity}"
                )

            update_data = BookUpdate(
                stock_quantity=new_quantity,
                in_stock=(new_quantity > 0),
            )

            return await self.update_book(book_id, update_data, regenerate_summary=False)
        except Exception as e:
            raise Exception(f"Error updating stock for book {book_id}: {str(e)}")

    # ==================== CATEGORY OPERATIONS ====================

    def create_category(self, category_data: BookCategoryCreate) -> BookCategory:
        """Create a new book category."""
        try:
            data = category_data.model_dump()
            doc_ref = self.db.collection(self.CATEGORIES_COLLECTION).document()
            doc_ref.set(data)

            return BookCategory(id=doc_ref.id, **category_data.model_dump())
        except Exception as e:
            raise Exception(f"Error creating category: {str(e)}")

    def get_all_categories(self) -> List[BookCategory]:
        """Fetch all book categories."""
        try:
            docs = self.db.collection(self.CATEGORIES_COLLECTION).stream()
            categories = [self._document_to_category(doc) for doc in docs]
            return categories
        except Exception as e:
            raise Exception(f"Error fetching categories: {str(e)}")

    def update_category(
        self, category_id: str, update_data: BookCategoryUpdate
    ) -> Optional[BookCategory]:
        """Update a book category."""
        try:
            doc_ref = self.db.collection(self.CATEGORIES_COLLECTION).document(category_id)

            if not doc_ref.get().exists:
                return None

            update_fields = {
                k: v for k, v in update_data.model_dump().items() if v is not None
            }
            doc_ref.update(update_fields)

            updated_doc = doc_ref.get()
            return self._document_to_category(updated_doc)
        except Exception as e:
            raise Exception(f"Error updating category {category_id}: {str(e)}")

    # ==================== REVIEW OPERATIONS ====================

    async def create_review(self, review_data: BookReviewCreate) -> BookReview:
        """Create a new book review."""
        try:
            now = datetime.now()
            data = {
                **review_data.model_dump(),
                "created_at": now,
                "updated_at": now,
            }

            doc_ref = self.db.collection(self.REVIEWS_COLLECTION).document()
            doc_ref.set(data)

            # Update book's average rating and review count
            await self._update_book_rating(review_data.book_id)

            return BookReview(
                id=doc_ref.id,
                created_at=now,
                updated_at=now,
                **review_data.model_dump(),
            )
        except Exception as e:
            raise Exception(f"Error creating review: {str(e)}")

    def get_reviews_for_book(self, book_id: str) -> List[BookReview]:
        """Fetch all reviews for a specific book."""
        try:
            docs = (
                self.db.collection(self.REVIEWS_COLLECTION)
                .where("book_id", "==", book_id)
                .stream()
            )
            reviews = [self._document_to_review(doc) for doc in docs]
            return reviews
        except Exception as e:
            raise Exception(f"Error fetching reviews for book {book_id}: {str(e)}")

    async def _update_book_rating(self, book_id: str) -> None:
        """Update a book's average rating based on all reviews."""
        try:
            reviews = self.get_reviews_for_book(book_id)

            if not reviews:
                return

            total_rating = sum(review.rating for review in reviews)
            avg_rating = total_rating / len(reviews)

            update_data = BookUpdate(rating=round(avg_rating, 2), review_count=len(reviews))
            await self.update_book(book_id, update_data, regenerate_summary=False)
        except Exception as e:
            print(f"Warning: Error updating book rating: {str(e)}")

    # ==================== HELPER METHODS ====================

    def _ensure_book_instance(self, book_or_id: Union[Book, str]) -> Optional[Book]:
        """Ensure downstream helpers always operate on a Book instance."""
        if isinstance(book_or_id, Book):
            return book_or_id
        if not book_or_id:
            return None
        return self.get_book_by_id(str(book_or_id))

    @staticmethod
    def _resolve_pdf_storage_path(book: Book) -> Optional[str]:
        """Resolve the Firebase Storage object path for a book PDF."""
        if not book:
            return None

        if book.pdf_file_name:
            return book.pdf_file_name.lstrip("/")

        if book.pdf_url:
            return BookService._extract_path_from_pdf_url(book.pdf_url)

        return None

    @staticmethod
    def _extract_path_from_pdf_url(pdf_url: str) -> Optional[str]:
        """Extract a storage object path from a public Firebase Storage URL."""
        if not pdf_url:
            return None

        trimmed = pdf_url.strip()
        if not trimmed:
            return None

        if trimmed.startswith("gs://"):
            path_parts = trimmed[5:].split("/", 1)
            if len(path_parts) == 2 and path_parts[1]:
                return path_parts[1]
            return None

        if trimmed.startswith(("http://", "https://")):
            parsed = urlparse(trimmed)
            if "firebasestorage.googleapis.com" in parsed.netloc and "/o/" in parsed.path:
                encoded_path = parsed.path.split("/o/", 1)[1]
                return unquote(encoded_path)

            # Support signed URLs where the filename is the last segment
            filename = parsed.path.rsplit("/", 1)[-1]
            if filename.lower().endswith(".pdf"):
                return filename
            return None

        return trimmed.lstrip("/")

    def _sort_books(self, books: List[Book], sort_by: str) -> List[Book]:
        """Sort books based on the specified criteria."""
        if sort_by == "price-low-to-high":
            return sorted(books, key=lambda b: b.price)
        elif sort_by == "price-high-to-low":
            return sorted(books, key=lambda b: b.price, reverse=True)
        elif sort_by == "newest":
            return sorted(books, key=lambda b: b.created_at, reverse=True)
        elif sort_by == "rating":
            return sorted(
                books, key=lambda b: b.rating if b.rating is not None else 0, reverse=True
            )
        elif sort_by == "title":
            return sorted(books, key=lambda b: b.title.lower())
        else:
            return books

    @staticmethod
    def _document_to_book(doc: DocumentSnapshot) -> Book:
        """Convert a Firestore document snapshot to a Book object."""
        data = doc.to_dict()
        return Book(
            id=doc.id,
            title=data.get("title"),
            author=data.get("author"),
            isbn=data.get("isbn"),
            description=data.get("description"),
            genre=data.get("genre"),
            language=data.get("language"),
            published_date=data.get("published_date"),
            page_count=data.get("page_count"),
            price=data.get("price"),
            original_price=data.get("original_price"),
            currency=data.get("currency", "USD"),
            in_stock=data.get("in_stock", True),
            stock_quantity=data.get("stock_quantity"),
            cover_image=data.get("cover_image"),
            cover_image_url=data.get("cover_image_url"),
            pdf_url=data.get("pdf_url") or data.get("pdfUrl"),
            pdf_file_name=data.get("pdf_file_name") or data.get("pdfFileName"),
            rating=data.get("rating"),
            review_count=data.get("review_count", 0),
            publisher=data.get("publisher"),
            edition=data.get("edition"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            is_new=data.get("is_new", False),
            is_featured=data.get("is_featured", False),
            discount=data.get("discount"),
        )

    @staticmethod
    def _document_to_category(doc: DocumentSnapshot) -> BookCategory:
        """Convert a Firestore document snapshot to a BookCategory object."""
        data = doc.to_dict()
        return BookCategory(
            id=doc.id,
            name=data.get("name"),
            description=data.get("description"),
            icon=data.get("icon"),
            book_count=data.get("book_count", 0),
        )

    @staticmethod
    def _document_to_review(doc: DocumentSnapshot) -> BookReview:
        """Convert a Firestore document snapshot to a BookReview object."""
        data = doc.to_dict()
        return BookReview(
            id=doc.id,
            book_id=data.get("book_id"),
            user_id=data.get("user_id"),
            user_name=data.get("user_name"),
            rating=data.get("rating"),
            title=data.get("title"),
            content=data.get("content"),
            helpful=data.get("helpful", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


# Convenience function to create a service instance
def get_book_service() -> BookService:
    """Create and return a book service instance."""
    return BookService()
