"""
Pytest configuration and fixtures for BookService tests.

Provides shared fixtures for:
- Firestore database mocking
- Book model fixtures
- Category model fixtures
- Review model fixtures
- PDF operation fixtures
- Service fixtures
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from app.services.book_service import BookService
from app.models.book import (
    Book,
    BookCreate,
    BookUpdate,
    BookCategory,
    BookCategoryCreate,
    BookReview,
    BookReviewCreate,
)
from langchain_core.documents import Document


# ==================== DATABASE FIXTURES ====================


@pytest.fixture
def mock_firestore_client():
    """Create a mocked Firestore client for testing."""
    mock_db = MagicMock()
    return mock_db


# ==================== BOOK FIXTURES ====================


@pytest.fixture
def sample_book_create():
    """Create a sample BookCreate object for testing."""
    return BookCreate(
        title="The Great Gatsby",
        author="F. Scott Fitzgerald",
        isbn="978-0-7432-7356-5",
        description="A novel set in the Jazz Age that has been acclaimed by generations of readers.",
        genre="Fiction",
        language="English",
        published_date=datetime(1925, 4, 10),
        page_count=180,
        price=12.99,
        original_price=15.99,
        currency="USD",
        in_stock=True,
        stock_quantity=50,
        cover_image_url="https://example.com/cover.jpg",
        pdf_url="gs://my-bucket/books/gatsby.pdf",
        publisher="Scribner",
        edition="First Edition",
        is_new=False,
        is_featured=True,
        discount=10.0,
    )


@pytest.fixture
def sample_book(sample_book_create):
    """Create a complete Book object with ID."""
    data = sample_book_create.model_dump()
    data.update({
        "id": "book_123",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "rating": 4.5,
        "review_count": 125,
    })
    return Book(**data)


@pytest.fixture
def sample_book_update():
    """Create a sample BookUpdate object for testing updates."""
    return BookUpdate(
        title="The Great Gatsby - Updated",
        price=11.99,
        in_stock=True,
        stock_quantity=40,
    )


@pytest.fixture
def book_firestore_data(sample_book):
    """Create Firestore document representation of a book."""
    return {
        "title": sample_book.title,
        "author": sample_book.author,
        "isbn": sample_book.isbn,
        "description": sample_book.description,
        "genre": sample_book.genre,
        "language": sample_book.language,
        "published_date": sample_book.published_date,
        "page_count": sample_book.page_count,
        "price": sample_book.price,
        "original_price": sample_book.original_price,
        "currency": sample_book.currency,
        "in_stock": sample_book.in_stock,
        "stock_quantity": sample_book.stock_quantity,
        "cover_image_url": sample_book.cover_image_url,
        "pdf_url": sample_book.pdf_url,
        "publisher": sample_book.publisher,
        "edition": sample_book.edition,
        "is_new": sample_book.is_new,
        "is_featured": sample_book.is_featured,
        "discount": sample_book.discount,
        "rating": sample_book.rating,
        "review_count": sample_book.review_count,
        "created_at": sample_book.created_at,
        "updated_at": sample_book.updated_at,
    }


# ==================== CATEGORY FIXTURES ====================


@pytest.fixture
def sample_category_create():
    """Create a sample BookCategoryCreate object for testing."""
    return BookCategoryCreate(
        name="Science Fiction",
        description="Books about futuristic technology and space exploration",
        icon="🚀",
    )


@pytest.fixture
def sample_category(sample_category_create):
    """Create a complete BookCategory object with ID."""
    return BookCategory(
        id="category_123",
        book_count=45,
        **sample_category_create.model_dump(),
    )


@pytest.fixture
def category_firestore_data(sample_category):
    """Create Firestore document representation of a category."""
    return {
        "name": sample_category.name,
        "description": sample_category.description,
        "icon": sample_category.icon,
        "book_count": sample_category.book_count,
    }


# ==================== REVIEW FIXTURES ====================


@pytest.fixture
def sample_review_create():
    """Create a sample BookReviewCreate object for testing."""
    return BookReviewCreate(
        book_id="book_123",
        user_id="user_456",
        user_name="John Doe",
        rating=5.0,
        title="Amazing Book!",
        content="This is an excellent book that I highly recommend to everyone.",
    )


@pytest.fixture
def sample_review(sample_review_create):
    """Create a complete BookReview object with ID."""
    return BookReview(
        id="review_123",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        helpful=42,
        **sample_review_create.model_dump(),
    )


@pytest.fixture
def review_firestore_data(sample_review):
    """Create Firestore document representation of a review."""
    return {
        "book_id": sample_review.book_id,
        "user_id": sample_review.user_id,
        "user_name": sample_review.user_name,
        "rating": sample_review.rating,
        "title": sample_review.title,
        "content": sample_review.content,
        "helpful": sample_review.helpful,
        "created_at": sample_review.created_at,
        "updated_at": sample_review.updated_at,
    }


# ==================== PDF FIXTURES ====================


@pytest.fixture
def sample_pdf_preview():
    """Create sample PDF preview text."""
    return """Chapter 1: The Beginning

    This is the beginning of our story. It all started on a quiet morning when the sun was rising over the horizon.

    Chapter 2: The Journey

    The journey was long and arduous, but every step brought us closer to our destination."""


@pytest.fixture
def mock_pdf_documents():
    """Create mock LangChain Document objects from PDF."""
    return [
        Document(
            page_content="Chapter 1: The Beginning\n\nThis is the beginning of our story.",
            metadata={"source": "document", "page": 0},
        ),
        Document(
            page_content="Chapter 2: The Journey\n\nThe journey was long and arduous.",
            metadata={"source": "document", "page": 1},
        ),
        Document(
            page_content="Chapter 3: The Conclusion\n\nAnd so it came to an end.",
            metadata={"source": "document", "page": 2},
        ),
    ]


# ==================== SERVICE FIXTURES ====================


@pytest.fixture
def book_service_with_mock_db(mock_firestore_client):
    """Create BookService with mocked Firestore database."""
    service = BookService()
    service.db = mock_firestore_client
    return service


# ==================== PYTEST CONFIGURATION ====================


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test (requires pytest-asyncio)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
