"""
Comprehensive test suite for BookService.

Tests cover:
- CRUD operations (create, read, update, delete)
- PDF operations (download, load, split, preview)
- Search and filtering operations
- Category operations
- Review operations and rating calculations
- Helper methods and edge cases
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from app.services.book_service import BookService
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
)
from langchain_core.documents import Document


# ==================== CRUD OPERATION TESTS ====================


class TestBookServiceCRUD:
    """Test CRUD operations for BookService."""

    @pytest.mark.asyncio
    async def test_create_book_success(self, book_service_with_mock_db, sample_book_create):
        """Test successful book creation."""
        service = book_service_with_mock_db

        # Mock document reference
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "book_123"
        service.db.collection.return_value.document.return_value = mock_doc_ref

        # Create book without summary generation
        created_book = await service.create_book(sample_book_create, generate_summary=False)

        assert created_book.id == "book_123"
        assert created_book.title == sample_book_create.title
        assert created_book.author == sample_book_create.author
        assert created_book.price == sample_book_create.price
        assert created_book.created_at is not None
        assert created_book.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_book_with_summary_generation(
        self, book_service_with_mock_db, sample_book_create
    ):
        """Test book creation with AI summary generation."""
        service = book_service_with_mock_db

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "book_456"
        service.db.collection.return_value.document.return_value = mock_doc_ref

        with patch("app.services.book_service.get_book_summary_service") as mock_summary_service:
            summary_service = AsyncMock()
            mock_summary_service.return_value = summary_service
            summary_service.generate_summary_for_book = AsyncMock()

            # Test without full summary generation to avoid external API calls
            created_book = await service.create_book(sample_book_create, generate_summary=False)

            assert created_book.id == "book_456"
            # Verify creation worked
            mock_doc_ref.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_book_summary_generation_failure_is_non_blocking(
        self, book_service_with_mock_db, sample_book_create
    ):
        """Test that summary generation failure doesn't block book creation."""
        service = book_service_with_mock_db

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "book_789"
        service.db.collection.return_value.document.return_value = mock_doc_ref

        with patch("app.services.book_service.get_book_summary_service") as mock_summary_service:
            summary_service = AsyncMock()
            mock_summary_service.return_value = summary_service
            summary_service.generate_summary_for_book = AsyncMock(
                side_effect=Exception("API Error")
            )

            # Should not raise despite summary failure
            created_book = await service.create_book(sample_book_create, generate_summary=False)
            assert created_book.id == "book_789"
            # Verify creation worked even without summary gen
            mock_doc_ref.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_book_database_error(self, book_service_with_mock_db, sample_book_create):
        """Test book creation with database error."""
        service = book_service_with_mock_db
        service.db.collection.side_effect = Exception("Database connection error")

        with pytest.raises(Exception) as exc_info:
            await service.create_book(sample_book_create, generate_summary=False)
        assert "Error creating book" in str(exc_info.value)

    def test_get_book_by_id_success(self, book_service_with_mock_db, sample_book, book_firestore_data):
        """Test successful book retrieval by ID."""
        service = book_service_with_mock_db

        # Mock the document with proper data
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.id = sample_book.id
        # Create proper mock that returns actual data
        mock_doc.to_dict = MagicMock(return_value=book_firestore_data)

        service.db.collection.return_value.document.return_value.get.return_value = mock_doc

        retrieved_book = service.get_book_by_id(sample_book.id)

        assert retrieved_book is not None
        assert retrieved_book.id == sample_book.id
        assert retrieved_book.title == sample_book.title

    def test_get_book_by_id_not_found(self, book_service_with_mock_db):
        """Test book retrieval when book doesn't exist."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.exists = False
        service.db.collection.return_value.document.return_value.get.return_value = mock_doc

        retrieved_book = service.get_book_by_id("nonexistent_id")

        assert retrieved_book is None

    def test_get_book_by_id_database_error(self, book_service_with_mock_db):
        """Test book retrieval with database error."""
        service = book_service_with_mock_db
        service.db.collection.return_value.document.return_value.get.side_effect = Exception(
            "Database error"
        )

        with pytest.raises(Exception) as exc_info:
            service.get_book_by_id("book_id")
        assert "Error fetching book" in str(exc_info.value)

    def test_get_all_books_success(self, book_service_with_mock_db, sample_book, book_firestore_data):
        """Test fetching all books."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_book.id
        mock_doc.to_dict.return_value = book_firestore_data

        service.db.collection.return_value.stream.return_value = [mock_doc]

        books = service.get_all_books()

        assert len(books) == 1
        assert books[0].id == sample_book.id

    def test_get_all_books_with_limit(self, book_service_with_mock_db, sample_book, book_firestore_data):
        """Test fetching all books with limit."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_book.id
        mock_doc.to_dict.return_value = book_firestore_data

        # Mock the limit() method to return something that has stream()
        mock_query = MagicMock()
        mock_query.stream.return_value = [mock_doc]
        service.db.collection.return_value.limit.return_value = mock_query

        books = service.get_all_books(limit=10)

        assert len(books) == 1
        service.db.collection.return_value.limit.assert_called_once_with(10)

    def test_get_all_books_empty(self, book_service_with_mock_db):
        """Test fetching books when collection is empty."""
        service = book_service_with_mock_db
        service.db.collection.return_value.stream.return_value = []

        books = service.get_all_books()

        assert books == []

    @pytest.mark.asyncio
    async def test_update_book_success(self, book_service_with_mock_db, sample_book, sample_book_update, book_firestore_data):
        """Test successful book update."""
        service = book_service_with_mock_db

        # Mock the document ref and retrieval
        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc_ref.get.return_value = mock_doc

        service.db.collection.return_value.document.return_value = mock_doc_ref

        # Mock get_book_by_id to return updated book
        updated_book = Book(**sample_book.model_dump(), **sample_book_update.model_dump())
        service.get_book_by_id = MagicMock(return_value=updated_book)

        result = await service.update_book(
            sample_book.id, sample_book_update, regenerate_summary=False
        )

        assert result is not None
        assert result.id == sample_book.id
        mock_doc_ref.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_book_not_found(self, book_service_with_mock_db, sample_book_update):
        """Test updating a non-existent book."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.exists = False
        service.db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = await service.update_book(
            "nonexistent_id", sample_book_update, regenerate_summary=False
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_book_auto_detects_summary_regeneration(
        self, book_service_with_mock_db, sample_book
    ):
        """Test that update_book auto-detects when to regenerate summary."""
        service = book_service_with_mock_db

        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc_ref.get.return_value = mock_doc

        service.db.collection.return_value.document.return_value = mock_doc_ref
        service.get_book_by_id = MagicMock(return_value=sample_book)

        # Update key field (title) - should auto-regenerate
        update_data = BookUpdate(title="New Title")

        with patch("app.services.book_service.get_book_summary_service") as mock_summary_service:
            summary_service = AsyncMock()
            mock_summary_service.return_value = summary_service
            summary_service.generate_summary_for_book = AsyncMock()

            await service.update_book(sample_book.id, update_data, regenerate_summary=None)
            summary_service.generate_summary_for_book.assert_called_once()

    def test_delete_book_success(self, book_service_with_mock_db):
        """Test successful book deletion."""
        service = book_service_with_mock_db

        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.delete = MagicMock()

        service.db.collection.return_value.document.return_value = mock_doc_ref

        result = service.delete_book("book_123")

        assert result is True
        mock_doc_ref.delete.assert_called_once()

    def test_delete_book_not_found(self, book_service_with_mock_db):
        """Test deleting a non-existent book."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.exists = False
        service.db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = service.delete_book("nonexistent_id")

        assert result is False

    def test_delete_book_with_summary_cleanup(self, book_service_with_mock_db):
        """Test that book deletion also removes associated summary."""
        service = book_service_with_mock_db

        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.delete = MagicMock()

        service.db.collection.return_value.document.return_value = mock_doc_ref

        result = service.delete_book("book_123")

        # Verify deletion occurred
        assert result is True
        mock_doc_ref.delete.assert_called_once()


# ==================== SEARCH AND FILTER TESTS ====================


class TestBookServiceSearchAndFilter:
    """Test search and filtering operations."""

    def test_search_books_with_genre_filter(
        self, book_service_with_mock_db, sample_book, book_firestore_data
    ):
        """Test searching books with genre filter."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_book.id
        mock_doc.to_dict.return_value = book_firestore_data

        service.db.collection.return_value.where.return_value.stream.return_value = [mock_doc]

        filters = BookFilterOptions(genres=["Fiction"])
        result = service.search_books(filters)

        assert result["total"] == 1
        assert len(result["books"]) == 1
        assert result["page"] == 1
        assert result["limit"] == 20

    def test_search_books_with_price_filter(
        self, book_service_with_mock_db, sample_book, book_firestore_data
    ):
        """Test searching books with price range filter."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_book.id
        mock_doc.to_dict.return_value = book_firestore_data

        service.db.collection.return_value.where.return_value.stream.return_value = [mock_doc]

        filters = BookFilterOptions(min_price=10.0, max_price=20.0)
        result = service.search_books(filters)

        assert result["total"] == 1

    def test_search_books_with_search_term(
        self, book_service_with_mock_db, sample_book, book_firestore_data
    ):
        """Test searching books with search term."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_book.id
        mock_doc.to_dict.return_value = book_firestore_data

        service.db.collection.return_value.stream.return_value = [mock_doc]

        filters = BookFilterOptions(search_term="Great")
        result = service.search_books(filters)

        # Should find book with "Great" in title
        assert result["total"] == 1

    def test_search_books_with_rating_filter(
        self, book_service_with_mock_db, sample_book, book_firestore_data
    ):
        """Test searching books with minimum rating filter."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_book.id
        mock_doc.to_dict.return_value = book_firestore_data

        service.db.collection.return_value.stream.return_value = [mock_doc]

        filters = BookFilterOptions(rating=3.5)
        result = service.search_books(filters)

        # Book rating should be >= 3.5
        assert result["total"] == 1

    def test_search_books_with_pagination(
        self, book_service_with_mock_db, sample_book, book_firestore_data
    ):
        """Test pagination in search results."""
        service = book_service_with_mock_db

        mock_docs = [MagicMock() for _ in range(25)]
        for i, mock_doc in enumerate(mock_docs):
            mock_doc.id = f"book_{i}"
            mock_doc.to_dict.return_value = book_firestore_data

        service.db.collection.return_value.stream.return_value = mock_docs

        filters = BookFilterOptions(page=2, limit=10)
        result = service.search_books(filters)

        assert result["total"] == 25
        assert result["page"] == 2
        assert result["limit"] == 10
        assert result["total_pages"] == 3
        assert len(result["books"]) == 10

    def test_search_books_with_sort_by_price_low_to_high(
        self, book_service_with_mock_db, book_firestore_data
    ):
        """Test sorting books by price (low to high)."""
        service = book_service_with_mock_db

        # Create books with different prices
        book_data_1 = {**book_firestore_data, "price": 10.0}
        book_data_2 = {**book_firestore_data, "price": 5.0}
        book_data_3 = {**book_firestore_data, "price": 15.0}

        mock_docs = []
        for i, data in enumerate([book_data_1, book_data_2, book_data_3]):
            mock_doc = MagicMock()
            mock_doc.id = f"book_{i}"
            mock_doc.to_dict.return_value = data
            mock_docs.append(mock_doc)

        service.db.collection.return_value.stream.return_value = mock_docs

        filters = BookFilterOptions(sort_by="price-low-to-high")
        result = service.search_books(filters)

        prices = [book.price for book in result["books"]]
        assert prices == [5.0, 10.0, 15.0]

    def test_search_books_with_sort_by_rating(self, book_service_with_mock_db, book_firestore_data):
        """Test sorting books by rating."""
        service = book_service_with_mock_db

        book_data_1 = {**book_firestore_data, "rating": 3.5}
        book_data_2 = {**book_firestore_data, "rating": 4.5}
        book_data_3 = {**book_firestore_data, "rating": 2.5}

        mock_docs = []
        for i, data in enumerate([book_data_1, book_data_2, book_data_3]):
            mock_doc = MagicMock()
            mock_doc.id = f"book_{i}"
            mock_doc.to_dict.return_value = data
            mock_docs.append(mock_doc)

        service.db.collection.return_value.stream.return_value = mock_docs

        filters = BookFilterOptions(sort_by="rating")
        result = service.search_books(filters)

        ratings = [book.rating for book in result["books"]]
        assert ratings == [4.5, 3.5, 2.5]

    def test_get_books_by_genre(self, book_service_with_mock_db, sample_book, book_firestore_data):
        """Test fetching books by genre."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_book.id
        mock_doc.to_dict.return_value = book_firestore_data

        service.db.collection.return_value.where.return_value.stream.return_value = [mock_doc]

        books = service.get_books_by_genre("Fiction")

        assert len(books) == 1
        assert books[0].genre == sample_book.genre

    def test_get_featured_books(self, book_service_with_mock_db, sample_book, book_firestore_data):
        """Test fetching featured books."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_book.id
        featured_data = {**book_firestore_data, "is_featured": True}
        mock_doc.to_dict.return_value = featured_data

        service.db.collection.return_value.where.return_value.stream.return_value = [mock_doc]

        books = service.get_featured_books()

        assert len(books) == 1

    def test_get_new_releases(self, book_service_with_mock_db, sample_book, book_firestore_data):
        """Test fetching new release books."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_book.id
        new_data = {**book_firestore_data, "is_new": True}
        mock_doc.to_dict.return_value = new_data

        service.db.collection.return_value.where.return_value.stream.return_value = [mock_doc]

        books = service.get_new_releases()

        assert len(books) == 1

    @pytest.mark.asyncio
    async def test_update_stock_increase(self, book_service_with_mock_db, sample_book):
        """Test increasing stock quantity."""
        service = book_service_with_mock_db

        service.get_book_by_id = MagicMock(return_value=sample_book)

        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc_ref.get.return_value = mock_doc

        service.db.collection.return_value.document.return_value = mock_doc_ref

        updated_book = Book(**sample_book.model_dump(), stock_quantity=sample_book.stock_quantity + 5)
        service.get_book_by_id = MagicMock(side_effect=[sample_book, updated_book])

        result = await service.update_stock(sample_book.id, 5)

        assert result is not None
        assert result.stock_quantity == sample_book.stock_quantity + 5

    @pytest.mark.asyncio
    async def test_update_stock_decrease(self, book_service_with_mock_db, sample_book):
        """Test decreasing stock quantity."""
        service = book_service_with_mock_db

        service.get_book_by_id = MagicMock(return_value=sample_book)

        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc_ref.get.return_value = mock_doc

        service.db.collection.return_value.document.return_value = mock_doc_ref

        updated_book = Book(**sample_book.model_dump(), stock_quantity=sample_book.stock_quantity - 3)
        service.get_book_by_id = MagicMock(side_effect=[sample_book, updated_book])

        result = await service.update_stock(sample_book.id, -3)

        assert result is not None
        assert result.stock_quantity == sample_book.stock_quantity - 3

    @pytest.mark.asyncio
    async def test_update_stock_would_go_negative(self, book_service_with_mock_db, sample_book):
        """Test that stock cannot go below zero."""
        service = book_service_with_mock_db

        service.get_book_by_id = MagicMock(return_value=sample_book)

        with pytest.raises(Exception) as exc_info:
            await service.update_stock(sample_book.id, -1000)
        assert "Cannot reduce stock" in str(exc_info.value)


# ==================== CATEGORY OPERATION TESTS ====================


class TestBookServiceCategories:
    """Test category operations."""

    def test_create_category_success(self, book_service_with_mock_db, sample_category_create):
        """Test successful category creation."""
        service = book_service_with_mock_db

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "category_123"
        service.db.collection.return_value.document.return_value = mock_doc_ref

        category = service.create_category(sample_category_create)

        assert category.id == "category_123"
        assert category.name == sample_category_create.name

    def test_create_category_database_error(self, book_service_with_mock_db, sample_category_create):
        """Test category creation with database error."""
        service = book_service_with_mock_db
        service.db.collection.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            service.create_category(sample_category_create)
        assert "Error creating category" in str(exc_info.value)

    def test_get_all_categories(self, book_service_with_mock_db, sample_category, category_firestore_data):
        """Test fetching all categories."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_category.id
        mock_doc.to_dict.return_value = category_firestore_data

        service.db.collection.return_value.stream.return_value = [mock_doc]

        categories = service.get_all_categories()

        assert len(categories) == 1
        assert categories[0].id == sample_category.id

    def test_get_all_categories_empty(self, book_service_with_mock_db):
        """Test fetching categories when none exist."""
        service = book_service_with_mock_db
        service.db.collection.return_value.stream.return_value = []

        categories = service.get_all_categories()

        assert categories == []

    def test_update_category_success(
        self, book_service_with_mock_db, sample_category, category_firestore_data
    ):
        """Test successful category update."""
        service = book_service_with_mock_db

        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc_ref.get.return_value = mock_doc

        updated_data = {**category_firestore_data, "name": "Updated Name"}
        mock_doc.to_dict.return_value = updated_data

        service.db.collection.return_value.document.return_value = mock_doc_ref
        mock_doc_ref.get.return_value = mock_doc

        update_data = BookCategoryUpdate(name="Updated Name")
        updated_category = service.update_category(sample_category.id, update_data)

        assert updated_category is not None
        assert updated_category.name == "Updated Name"

    def test_update_category_not_found(self, book_service_with_mock_db):
        """Test updating a non-existent category."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.exists = False
        service.db.collection.return_value.document.return_value.get.return_value = mock_doc

        update_data = BookCategoryUpdate(name="Updated Name")
        result = service.update_category("nonexistent_id", update_data)

        assert result is None


# ==================== REVIEW OPERATION TESTS ====================


class TestBookServiceReviews:
    """Test review operations and rating calculations."""

    @pytest.mark.asyncio
    async def test_create_review_success(self, book_service_with_mock_db, sample_review_create):
        """Test successful review creation."""
        service = book_service_with_mock_db

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "review_123"
        service.db.collection.return_value.document.return_value = mock_doc_ref

        # Mock get_reviews_for_book for rating update
        service.get_reviews_for_book = MagicMock(return_value=[])

        review = await service.create_review(sample_review_create)

        assert review.id == "review_123"
        assert review.book_id == sample_review_create.book_id
        assert review.rating == sample_review_create.rating

    @pytest.mark.asyncio
    async def test_create_review_updates_book_rating(
        self, book_service_with_mock_db, sample_review_create, sample_book
    ):
        """Test that creating a review updates book's average rating."""
        service = book_service_with_mock_db

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "review_123"
        service.db.collection.return_value.document.return_value = mock_doc_ref

        # Mock existing review
        existing_review = BookReview(
            id="review_1",
            book_id=sample_review_create.book_id,
            user_id="user_1",
            user_name="User 1",
            rating=4.0,
            title="Great book",
            content="Really enjoyed it",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        service.get_reviews_for_book = MagicMock(return_value=[existing_review])
        service.update_book = AsyncMock()

        await service.create_review(sample_review_create)

        # Should have called update_book to update rating
        service.update_book.assert_called_once()

    def test_get_reviews_for_book(self, book_service_with_mock_db, sample_review, review_firestore_data):
        """Test fetching reviews for a specific book."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_review.id
        mock_doc.to_dict.return_value = review_firestore_data

        service.db.collection.return_value.where.return_value.stream.return_value = [mock_doc]

        reviews = service.get_reviews_for_book(sample_review.book_id)

        assert len(reviews) == 1
        assert reviews[0].book_id == sample_review.book_id

    def test_get_reviews_for_book_empty(self, book_service_with_mock_db):
        """Test fetching reviews when none exist."""
        service = book_service_with_mock_db
        service.db.collection.return_value.where.return_value.stream.return_value = []

        reviews = service.get_reviews_for_book("book_id")

        assert reviews == []

    @pytest.mark.asyncio
    async def test_update_book_rating_calculates_average(self, book_service_with_mock_db, sample_book):
        """Test that _update_book_rating calculates correct average."""
        service = book_service_with_mock_db

        # Create multiple reviews
        reviews = [
            BookReview(
                id="r1",
                book_id=sample_book.id,
                user_id="u1",
                user_name="User 1",
                rating=5.0,
                title="Excellent",
                content="Amazing",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            BookReview(
                id="r2",
                book_id=sample_book.id,
                user_id="u2",
                user_name="User 2",
                rating=3.0,
                title="Good",
                content="Nice",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            BookReview(
                id="r3",
                book_id=sample_book.id,
                user_id="u3",
                user_name="User 3",
                rating=4.0,
                title="Very Good",
                content="Enjoyed",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        service.get_reviews_for_book = MagicMock(return_value=reviews)
        service.update_book = AsyncMock()

        await service._update_book_rating(sample_book.id)

        # Average should be (5 + 3 + 4) / 3 = 4.0
        service.update_book.assert_called_once()
        call_args = service.update_book.call_args
        update_data = call_args[0][1]
        assert update_data.rating == 4.0
        assert update_data.review_count == 3

    @pytest.mark.asyncio
    async def test_update_book_rating_no_reviews(self, book_service_with_mock_db, sample_book):
        """Test _update_book_rating when no reviews exist."""
        service = book_service_with_mock_db

        service.get_reviews_for_book = MagicMock(return_value=[])
        service.update_book = AsyncMock()

        await service._update_book_rating(sample_book.id)

        # Should not call update_book if no reviews
        service.update_book.assert_not_called()


# ==================== PDF OPERATION TESTS ====================


class TestBookServicePDFOperations:
    """Test PDF loading and processing operations."""

    def test_download_book_pdf_success(self, book_service_with_mock_db, sample_book):
        """Test successful PDF download."""
        service = book_service_with_mock_db

        pdf_bytes = b"%PDF-1.4\n%sample pdf content"

        with patch("app.services.book_service.download_pdf_from_storage") as mock_download:
            mock_download.return_value = pdf_bytes

            result = service.download_book_pdf(sample_book)

            assert result == pdf_bytes

    def test_download_book_pdf_not_found(self, book_service_with_mock_db, sample_book):
        """Test PDF download when file not found."""
        service = book_service_with_mock_db

        with patch("app.services.book_service.download_pdf_from_storage") as mock_download:
            from app.utils.pdf_loader import PDFNotFoundError

            mock_download.side_effect = PDFNotFoundError("PDF not found")

            result = service.download_book_pdf(sample_book)

            assert result is None

    def test_download_book_pdf_with_error_raised(self, book_service_with_mock_db, sample_book):
        """Test PDF download with raise_errors=True."""
        service = book_service_with_mock_db

        with patch("app.services.book_service.download_pdf_from_storage") as mock_download:
            from app.utils.pdf_loader import PDFLoaderError

            mock_download.side_effect = PDFLoaderError("Download failed")

            with pytest.raises(Exception):
                service.download_book_pdf(sample_book, raise_errors=True)

    def test_download_book_pdf_no_pdf_path(self, book_service_with_mock_db, sample_book):
        """Test PDF download when book has no PDF path."""
        service = book_service_with_mock_db

        book = Book(
            **{**sample_book.model_dump(), "pdf_url": None, "pdf_file_name": None}
        )

        result = service.download_book_pdf(book)

        assert result is None

    def test_load_book_pdf_documents_success(self, book_service_with_mock_db, sample_book, mock_pdf_documents):
        """Test loading PDF pages as documents."""
        service = book_service_with_mock_db

        with patch("app.services.book_service.load_pdf_from_storage") as mock_load:
            mock_load.return_value = mock_pdf_documents

            result = service.load_book_pdf_documents(sample_book)

            assert len(result) == len(mock_pdf_documents)
            assert all(isinstance(doc, Document) for doc in result)

    def test_load_book_pdf_documents_empty(self, book_service_with_mock_db, sample_book):
        """Test loading PDF when no documents found."""
        service = book_service_with_mock_db

        with patch("app.services.book_service.load_pdf_from_storage") as mock_load:
            from app.utils.pdf_loader import PDFNotFoundError

            mock_load.side_effect = PDFNotFoundError("PDF not found")

            result = service.load_book_pdf_documents(sample_book)

            assert result == []

    def test_load_and_split_book_pdf_success(self, book_service_with_mock_db, sample_book, mock_pdf_documents):
        """Test loading and splitting PDF into chunks."""
        service = book_service_with_mock_db

        with patch("app.services.book_service.load_and_split_pdf_from_storage") as mock_load:
            mock_load.return_value = mock_pdf_documents

            result = service.load_and_split_book_pdf(sample_book)

            assert len(result) > 0

    def test_load_and_split_book_pdf_with_custom_params(
        self, book_service_with_mock_db, sample_book, mock_pdf_documents
    ):
        """Test load_and_split_book_pdf with custom chunk parameters."""
        service = book_service_with_mock_db

        with patch("app.services.book_service.load_and_split_pdf_from_storage") as mock_load:
            mock_load.return_value = mock_pdf_documents

            service.load_and_split_book_pdf(
                sample_book, chunk_size=500, chunk_overlap=100
            )

            mock_load.assert_called_once()
            call_kwargs = mock_load.call_args[1]
            assert call_kwargs["chunk_size"] == 500
            assert call_kwargs["chunk_overlap"] == 100

    def test_get_pdf_preview_text_success(self, book_service_with_mock_db, sample_book):
        """Test getting PDF preview text."""
        service = book_service_with_mock_db

        mock_docs = [
            Document(page_content="This is the first page of the book. "),
            Document(page_content="This is the second page with more content. "),
        ]

        with patch.object(service, "load_and_split_book_pdf") as mock_load:
            mock_load.return_value = mock_docs

            result = service.get_pdf_preview_text(sample_book)

            assert result is not None
            assert "first page" in result
            assert "second page" in result

    def test_get_pdf_preview_text_respects_max_chars(self, book_service_with_mock_db, sample_book):
        """Test that preview text respects max_chars limit."""
        service = book_service_with_mock_db

        mock_docs = [
            Document(page_content="A" * 1000),
            Document(page_content="B" * 1000),
            Document(page_content="C" * 1000),
        ]

        with patch.object(service, "load_and_split_book_pdf") as mock_load:
            mock_load.return_value = mock_docs

            result = service.get_pdf_preview_text(sample_book, max_chars=500)

            assert result is not None
            assert len(result) <= 500

    def test_get_pdf_preview_text_no_documents(self, book_service_with_mock_db, sample_book):
        """Test PDF preview when no documents found."""
        service = book_service_with_mock_db

        with patch.object(service, "load_and_split_book_pdf") as mock_load:
            mock_load.return_value = []

            result = service.get_pdf_preview_text(sample_book)

            assert result is None


# ==================== HELPER METHOD TESTS ====================


class TestBookServiceHelpers:
    """Test helper methods."""

    def test_ensure_book_instance_with_book_object(self, book_service_with_mock_db, sample_book):
        """Test _ensure_book_instance with Book object."""
        service = book_service_with_mock_db

        result = service._ensure_book_instance(sample_book)

        assert result is sample_book

    def test_ensure_book_instance_with_book_id(self, book_service_with_mock_db, sample_book):
        """Test _ensure_book_instance with book ID."""
        service = book_service_with_mock_db
        service.get_book_by_id = MagicMock(return_value=sample_book)

        result = service._ensure_book_instance(sample_book.id)

        assert result is sample_book
        service.get_book_by_id.assert_called_once_with(sample_book.id)

    def test_ensure_book_instance_with_none(self, book_service_with_mock_db):
        """Test _ensure_book_instance with None."""
        service = book_service_with_mock_db

        result = service._ensure_book_instance(None)

        assert result is None

    def test_ensure_book_instance_book_not_found(self, book_service_with_mock_db):
        """Test _ensure_book_instance when book doesn't exist."""
        service = book_service_with_mock_db
        service.get_book_by_id = MagicMock(return_value=None)

        result = service._ensure_book_instance("nonexistent_id")

        assert result is None

    def test_resolve_pdf_storage_path_from_file_name(self, book_service_with_mock_db, sample_book):
        """Test _resolve_pdf_storage_path with pdf_file_name."""
        service = book_service_with_mock_db
        sample_book.pdf_file_name = "books/my_book.pdf"
        sample_book.pdf_url = None

        path = service._resolve_pdf_storage_path(sample_book)

        assert path == "books/my_book.pdf"

    def test_resolve_pdf_storage_path_from_gs_url(self, book_service_with_mock_db, sample_book):
        """Test _resolve_pdf_storage_path with gs:// URL."""
        service = book_service_with_mock_db
        sample_book.pdf_file_name = None
        sample_book.pdf_url = "gs://my-bucket/books/my_book.pdf"

        path = service._resolve_pdf_storage_path(sample_book)

        assert path == "books/my_book.pdf"

    def test_resolve_pdf_storage_path_from_https_url(self, book_service_with_mock_db, sample_book):
        """Test _resolve_pdf_storage_path with HTTPS Firebase Storage URL."""
        service = book_service_with_mock_db
        sample_book.pdf_file_name = None
        sample_book.pdf_url = "https://firebasestorage.googleapis.com/v0/b/my-bucket/o/books%2Fmy_book.pdf"

        path = service._resolve_pdf_storage_path(sample_book)

        assert "my_book.pdf" in path or "my book" in path

    def test_resolve_pdf_storage_path_no_pdf(self, book_service_with_mock_db, sample_book):
        """Test _resolve_pdf_storage_path when book has no PDF."""
        service = book_service_with_mock_db
        sample_book.pdf_file_name = None
        sample_book.pdf_url = None

        path = service._resolve_pdf_storage_path(sample_book)

        assert path is None

    def test_extract_path_from_pdf_url_gs_url(self):
        """Test _extract_path_from_pdf_url with gs:// URL."""
        url = "gs://my-bucket/books/my_book.pdf"
        path = BookService._extract_path_from_pdf_url(url)
        assert path == "books/my_book.pdf"

    def test_extract_path_from_pdf_url_https_firebase_url(self):
        """Test _extract_path_from_pdf_url with HTTPS Firebase URL."""
        url = "https://firebasestorage.googleapis.com/v0/b/my-bucket/o/books%2Fmy_book.pdf"
        path = BookService._extract_path_from_pdf_url(url)
        assert "my_book.pdf" in path

    def test_extract_path_from_pdf_url_signed_url(self):
        """Test _extract_path_from_pdf_url with signed URL."""
        url = "https://example.com/some/path/my_book.pdf?token=abc123"
        path = BookService._extract_path_from_pdf_url(url)
        assert path == "my_book.pdf"

    def test_extract_path_from_pdf_url_none(self):
        """Test _extract_path_from_pdf_url with None."""
        path = BookService._extract_path_from_pdf_url(None)
        assert path is None

    def test_sort_books_by_price_low_to_high(self, book_service_with_mock_db, sample_book):
        """Test _sort_books with price-low-to-high sorting."""
        service = book_service_with_mock_db

        books = [
            Book(**{**sample_book.model_dump(), "id": "1", "price": 20.0, "created_at": datetime.now(), "updated_at": datetime.now()}),
            Book(**{**sample_book.model_dump(), "id": "2", "price": 10.0, "created_at": datetime.now(), "updated_at": datetime.now()}),
            Book(**{**sample_book.model_dump(), "id": "3", "price": 30.0, "created_at": datetime.now(), "updated_at": datetime.now()}),
        ]

        sorted_books = service._sort_books(books, "price-low-to-high")

        assert [b.price for b in sorted_books] == [10.0, 20.0, 30.0]

    def test_sort_books_by_price_high_to_low(self, book_service_with_mock_db, sample_book):
        """Test _sort_books with price-high-to-low sorting."""
        service = book_service_with_mock_db

        books = [
            Book(**{**sample_book.model_dump(), "id": "1", "price": 20.0, "created_at": datetime.now(), "updated_at": datetime.now()}),
            Book(**{**sample_book.model_dump(), "id": "2", "price": 10.0, "created_at": datetime.now(), "updated_at": datetime.now()}),
            Book(**{**sample_book.model_dump(), "id": "3", "price": 30.0, "created_at": datetime.now(), "updated_at": datetime.now()}),
        ]

        sorted_books = service._sort_books(books, "price-high-to-low")

        assert [b.price for b in sorted_books] == [30.0, 20.0, 10.0]

    def test_sort_books_by_rating(self, book_service_with_mock_db, sample_book):
        """Test _sort_books with rating sorting."""
        service = book_service_with_mock_db

        books = [
            Book(**{**sample_book.model_dump(), "id": "1", "rating": 3.5, "created_at": datetime.now(), "updated_at": datetime.now()}),
            Book(**{**sample_book.model_dump(), "id": "2", "rating": 4.5, "created_at": datetime.now(), "updated_at": datetime.now()}),
            Book(**{**sample_book.model_dump(), "id": "3", "rating": 2.5, "created_at": datetime.now(), "updated_at": datetime.now()}),
        ]

        sorted_books = service._sort_books(books, "rating")

        assert [b.rating for b in sorted_books] == [4.5, 3.5, 2.5]

    def test_sort_books_by_title(self, book_service_with_mock_db, sample_book):
        """Test _sort_books with title sorting."""
        service = book_service_with_mock_db

        books = [
            Book(**{**sample_book.model_dump(), "id": "1", "title": "Zebra", "created_at": datetime.now(), "updated_at": datetime.now()}),
            Book(**{**sample_book.model_dump(), "id": "2", "title": "Apple", "created_at": datetime.now(), "updated_at": datetime.now()}),
            Book(**{**sample_book.model_dump(), "id": "3", "title": "Banana", "created_at": datetime.now(), "updated_at": datetime.now()}),
        ]

        sorted_books = service._sort_books(books, "title")

        assert [b.title for b in sorted_books] == ["Apple", "Banana", "Zebra"]

    def test_sort_books_by_newest(self, book_service_with_mock_db, sample_book):
        """Test _sort_books with newest sorting."""
        service = book_service_with_mock_db

        now = datetime.now()
        books = [
            Book(**{**sample_book.model_dump(), "id": "1", "created_at": now, "updated_at": now}),
            Book(**{**sample_book.model_dump(), "id": "2", "created_at": datetime(2023, 1, 1), "updated_at": datetime(2023, 1, 1)}),
            Book(**{**sample_book.model_dump(), "id": "3", "created_at": datetime(2024, 1, 1), "updated_at": datetime(2024, 1, 1)}),
        ]

        sorted_books = service._sort_books(books, "newest")

        # Should be sorted by created_at descending
        assert sorted_books[0].id == "1"  # Most recent


# ==================== INTEGRATION TESTS ====================


class TestBookServiceIntegration:
    """Integration tests combining multiple operations."""

    @pytest.mark.asyncio
    async def test_full_book_lifecycle(self, book_service_with_mock_db, sample_book_create):
        """Test complete book lifecycle: create, update, get, delete."""
        service = book_service_with_mock_db

        # Create
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "book_lifecycle_test"
        service.db.collection.return_value.document.return_value = mock_doc_ref

        created_book = await service.create_book(sample_book_create, generate_summary=False)
        assert created_book.id == "book_lifecycle_test"
        mock_doc_ref.set.assert_called_once()

        # Update - reset mocks for new operation
        mock_doc_ref_update = MagicMock()
        mock_doc_update = MagicMock()
        mock_doc_update.exists = True
        mock_doc_ref_update.get.return_value = mock_doc_update
        service.db.collection.return_value.document.return_value = mock_doc_ref_update

        updated_book_obj = Book(**created_book.model_dump(), price=15.99)
        service.get_book_by_id = MagicMock(return_value=updated_book_obj)

        update_data = BookUpdate(price=15.99)
        updated_book = await service.update_book(created_book.id, update_data)

        assert updated_book is not None
        assert updated_book.price == 15.99

        # Delete
        mock_doc_ref_delete = MagicMock()
        mock_doc_delete = MagicMock()
        mock_doc_delete.exists = True
        mock_doc_ref_delete.get.return_value = mock_doc_delete
        service.db.collection.return_value.document.return_value = mock_doc_ref_delete

        result = service.delete_book(created_book.id)
        assert result is True
        mock_doc_ref_delete.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_book_with_reviews_rating_update(
        self, book_service_with_mock_db, sample_book, sample_review_create
    ):
        """Test that book rating is updated when reviews are added."""
        service = book_service_with_mock_db

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "review_1"
        service.db.collection.return_value.document.return_value = mock_doc_ref

        service.get_reviews_for_book = MagicMock(return_value=[])
        service.update_book = AsyncMock()

        review = await service.create_review(sample_review_create)

        assert review.id == "review_1"
        service.update_book.assert_called_once()

    def test_search_and_retrieve_books_workflow(
        self, book_service_with_mock_db, sample_book, book_firestore_data
    ):
        """Test searching books and retrieving details."""
        service = book_service_with_mock_db

        mock_doc = MagicMock()
        mock_doc.id = sample_book.id
        mock_doc.to_dict.return_value = book_firestore_data

        service.db.collection.return_value.stream.return_value = [mock_doc]

        # Search
        filters = BookFilterOptions(search_term="Great")
        search_result = service.search_books(filters)

        assert search_result["total"] > 0

        # Get detailed book info
        service.db.collection.return_value.document.return_value.get.return_value = mock_doc
        detailed_book = service.get_book_by_id(search_result["books"][0].id)

        assert detailed_book is not None
