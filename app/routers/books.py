"""
Books Router

Handles book-related operations including:
- CRUD operations for books
- Searching and filtering books
- Category management
- Book reviews
- Stock management
"""

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
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
from app.models.book_summary import (
    BookSummary,
    SummaryGenerationRequest,
    SummaryGenerationResponse,
)
from app.services.book_service import get_book_service
from app.services.book_summary_service import get_book_summary_service
from app.services.book_viewer_service import (
    get_book_viewer_service,
    BookViewerError,
    BookNotFoundError,
    PdfNotFoundError,
)
from app.models.book_viewer import BookViewerPayload

router = APIRouter(prefix="/api/books", tags=["books"])


# ==================== BOOK CRUD ENDPOINTS ====================


@router.post("", status_code=201)
async def create_book(
    book_data: BookCreate,
    generate_summary: bool = Query(True, description="Auto-generate AI summary")
):
    """
    Create a new book in the bookstore.
    Automatically generates AI-powered summary by default.

    Args:
        book_data (BookCreate): The book data to create
        generate_summary (bool): Whether to generate AI summary (default: True)

    Returns:
        Book: The created book with ID

    Raises:
        HTTPException: 400 if invalid data, 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        book = await book_service.create_book(book_data, generate_summary=generate_summary)
        return book.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating book: {str(e)}")


@router.get("/{book_id}")
async def get_book(book_id: str = Path(..., description="The book ID")):
    """
    Fetch a book by its ID.

    Args:
        book_id (str): The unique identifier of the book

    Returns:
        Book: The book data

    Raises:
        HTTPException: 404 if book not found, 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        book = book_service.get_book_by_id(book_id)

        if book is None:
            raise HTTPException(status_code=404, detail=f"Book with ID '{book_id}' not found")

        return book.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching book: {str(e)}")


@router.get("/{book_id}/viewer", response_model=BookViewerPayload)
async def get_book_viewer(book_id: str = Path(..., description="The book ID")):
    """
    Fetch metadata required for the book PDF viewer.

    Returns book details, PDF metadata, and the streaming URL for the PDF asset.
    """
    viewer_service = get_book_viewer_service()

    try:
        payload = viewer_service.get_viewer_payload(book_id)
        return payload
    except BookNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PdfNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except BookViewerError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{book_id}/viewer/stream")
async def stream_book_pdf(book_id: str = Path(..., description="The book ID")):
    """
    Stream the PDF asset associated with a book for the viewer.
    """
    viewer_service = get_book_viewer_service()

    try:
        payload = viewer_service.get_viewer_payload(book_id)
        file_handle = viewer_service.open_pdf(book_id)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PdfNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except BookViewerError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    metadata = payload.pdf

    headers = {
        "Content-Disposition": f'inline; filename="{metadata.filename}"',
        "Content-Length": str(metadata.file_size),
    }

    return StreamingResponse(file_handle, media_type=metadata.mime_type, headers=headers)


@router.get("")
async def get_all_books(limit: Optional[int] = Query(None, ge=1, le=100)):
    """
    Fetch all books from the bookstore.

    Args:
        limit (Optional[int]): Maximum number of books to return

    Returns:
        list: List of all books

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        books = book_service.get_all_books(limit=limit)
        return [book.model_dump() for book in books]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching books: {str(e)}")


@router.patch("/{book_id}")
async def update_book(
    book_id: str = Path(..., description="The book ID"),
    update_data: BookUpdate = None,
    regenerate_summary: Optional[bool] = Query(
        None,
        description="Regenerate AI summary. If null, auto-detects based on updated fields"
    ),
):
    """
    Update an existing book.
    Automatically regenerates AI summary if key fields (title, author, description, genre) are updated.

    Args:
        book_id (str): The ID of the book to update
        update_data (BookUpdate): The data to update
        regenerate_summary (Optional[bool]): Force regenerate summary. If None, auto-detects.

    Returns:
        Book: The updated book

    Raises:
        HTTPException: 400 if invalid data, 404 if book not found, 500 if database error occurs
    """
    try:
        if not update_data:
            raise HTTPException(status_code=400, detail="Update data is required")

        book_service = get_book_service()
        updated_book = await book_service.update_book(
            book_id,
            update_data,
            regenerate_summary=regenerate_summary
        )

        if updated_book is None:
            raise HTTPException(status_code=404, detail=f"Book with ID '{book_id}' not found")

        return updated_book.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating book: {str(e)}")


@router.delete("/{book_id}")
async def delete_book(book_id: str = Path(..., description="The book ID")):
    """
    Delete a book from the bookstore.

    Args:
        book_id (str): The ID of the book to delete

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: 404 if book not found, 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        success = book_service.delete_book(book_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Book with ID '{book_id}' not found")

        return {"status": "success", "message": f"Book '{book_id}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting book: {str(e)}")


# ==================== SEARCH AND FILTER ENDPOINTS ====================


@router.post("/search")
async def search_books(filters: BookFilterOptions):
    """
    Search and filter books based on various criteria.

    Supports:
    - Genre filtering
    - Price range filtering
    - Rating filtering
    - In-stock filtering
    - Search by title/author
    - Sorting (price, rating, newest, title)
    - Pagination

    Args:
        filters (BookFilterOptions): Filter options for the search

    Returns:
        dict: Search results with books, pagination info, and totals

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        result = book_service.search_books(filters)

        return {
            "books": [book.model_dump() for book in result["books"]],
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"],
            "total_pages": result["total_pages"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching books: {str(e)}")


@router.get("/genre/{genre}")
async def get_books_by_genre(
    genre: str = Path(..., description="The genre to filter by"),
    limit: Optional[int] = Query(None, ge=1, le=100),
):
    """
    Fetch books by genre.

    Args:
        genre (str): The genre to filter by
        limit (Optional[int]): Maximum number of books to return

    Returns:
        list: List of books in the specified genre

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        books = book_service.get_books_by_genre(genre, limit=limit)
        return [book.model_dump() for book in books]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching books by genre: {str(e)}")


@router.get("/featured/list")
async def get_featured_books(limit: Optional[int] = Query(10, ge=1, le=100)):
    """
    Fetch featured books.

    Args:
        limit (Optional[int]): Maximum number of books to return (default: 10)

    Returns:
        list: List of featured books

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        books = book_service.get_featured_books(limit=limit)
        return [book.model_dump() for book in books]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching featured books: {str(e)}")


@router.get("/new-releases/list")
async def get_new_releases(limit: Optional[int] = Query(10, ge=1, le=100)):
    """
    Fetch new release books.

    Args:
        limit (Optional[int]): Maximum number of books to return (default: 10)

    Returns:
        list: List of new release books

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        books = book_service.get_new_releases(limit=limit)
        return [book.model_dump() for book in books]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching new releases: {str(e)}")


# ==================== STOCK MANAGEMENT ENDPOINTS ====================


@router.patch("/{book_id}/stock")
async def update_book_stock(
    book_id: str = Path(..., description="The book ID"),
    quantity_change: int = Query(..., description="Amount to change stock by (positive or negative)"),
):
    """
    Update book stock quantity.

    Args:
        book_id (str): The ID of the book
        quantity_change (int): Amount to change (positive to add, negative to reduce)

    Returns:
        Book: The updated book with new stock quantity

    Raises:
        HTTPException: 400 if stock would go negative, 404 if book not found, 500 if error occurs
    """
    try:
        book_service = get_book_service()
        updated_book = await book_service.update_stock(book_id, quantity_change)

        if updated_book is None:
            raise HTTPException(status_code=404, detail=f"Book with ID '{book_id}' not found")

        return updated_book.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating stock: {str(e)}")


# ==================== CATEGORY ENDPOINTS ====================


@router.post("/categories", status_code=201)
async def create_category(category_data: BookCategoryCreate):
    """
    Create a new book category.

    Args:
        category_data (BookCategoryCreate): The category data to create

    Returns:
        BookCategory: The created category

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        category = book_service.create_category(category_data)
        return category.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating category: {str(e)}")


@router.get("/categories")
async def get_all_categories():
    """
    Fetch all book categories.

    Returns:
        list: List of all categories

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        categories = book_service.get_all_categories()
        return [category.model_dump() for category in categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")


@router.patch("/categories/{category_id}")
async def update_category(
    category_id: str = Path(..., description="The category ID"),
    update_data: BookCategoryUpdate = None,
):
    """
    Update a book category.

    Args:
        category_id (str): The ID of the category to update
        update_data (BookCategoryUpdate): The data to update

    Returns:
        BookCategory: The updated category

    Raises:
        HTTPException: 400 if invalid data, 404 if category not found, 500 if error occurs
    """
    try:
        if not update_data:
            raise HTTPException(status_code=400, detail="Update data is required")

        book_service = get_book_service()
        updated_category = book_service.update_category(category_id, update_data)

        if updated_category is None:
            raise HTTPException(
                status_code=404, detail=f"Category with ID '{category_id}' not found"
            )

        return updated_category.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating category: {str(e)}")


# ==================== REVIEW ENDPOINTS ====================


@router.post("/reviews", status_code=201)
async def create_review(review_data: BookReviewCreate):
    """
    Create a new book review.

    Automatically updates the book's average rating and review count.

    Args:
        review_data (BookReviewCreate): The review data to create

    Returns:
        BookReview: The created review

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        review = await book_service.create_review(review_data)
        return review.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating review: {str(e)}")


@router.get("/{book_id}/reviews")
async def get_book_reviews(book_id: str = Path(..., description="The book ID")):
    """
    Fetch all reviews for a specific book.

    Args:
        book_id (str): The ID of the book

    Returns:
        list: List of all reviews for the book

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        book_service = get_book_service()
        reviews = book_service.get_reviews_for_book(book_id)
        return [review.model_dump() for review in reviews]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching reviews for book: {str(e)}"
        )


# ==================== BOOK SUMMARY ENDPOINTS ====================


@router.get("/{book_id}/summary", response_model=BookSummary)
async def get_book_summary(book_id: str = Path(..., description="The book ID")):
    """
    Fetch AI-generated summary for a book.

    Args:
        book_id (str): The book ID

    Returns:
        BookSummary: AI-generated summary with themes, tags, and recommendations

    Raises:
        HTTPException: 404 if summary not found, 500 if error occurs
    """
    try:
        summary_service = get_book_summary_service()
        summary = summary_service.get_summary_by_book_id(book_id)

        if summary is None:
            raise HTTPException(
                status_code=404,
                detail=f"Summary for book '{book_id}' not found. Try generating one first."
            )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching book summary: {str(e)}"
        )


@router.post("/{book_id}/summary/generate", response_model=SummaryGenerationResponse)
async def generate_book_summary(
    book_id: str = Path(..., description="The book ID"),
    force_regenerate: bool = Query(
        False,
        description="Force regeneration even if summary exists"
    ),
):
    """
    Generate AI-powered summary for a book.

    Uses ChatGPT-4 to analyze the book and generate:
    - Short and detailed summaries
    - Key themes
    - Target audience
    - Mood tags
    - Content warnings
    - Similar books tags
    - Compelling reason to read

    Args:
        book_id (str): The book ID
        force_regenerate (bool): Force regeneration (default: False)

    Returns:
        SummaryGenerationResponse: Generated summary with metadata

    Raises:
        HTTPException: 404 if book not found, 500 if error occurs
    """
    try:
        # Fetch the book
        book_service = get_book_service()
        book = book_service.get_book_by_id(book_id)

        if book is None:
            return SummaryGenerationResponse(
                success=False,
                error=f"Book with ID '{book_id}' not found"
            )

        # Generate summary
        summary_service = get_book_summary_service()
        summary = await summary_service.generate_summary_for_book(
            book,
            force_regenerate=force_regenerate
        )

        return SummaryGenerationResponse(
            success=True,
            summary=summary,
            message=f"Summary generated successfully for '{book.title}'"
        )

    except Exception as e:
        return SummaryGenerationResponse(
            success=False,
            error=f"Error generating summary: {str(e)}"
        )


@router.delete("/{book_id}/summary")
async def delete_book_summary(book_id: str = Path(..., description="The book ID")):
    """
    Delete AI-generated summary for a book.

    Args:
        book_id (str): The book ID

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: 404 if summary not found, 500 if error occurs
    """
    try:
        summary_service = get_book_summary_service()
        success = summary_service.delete_summary_by_book_id(book_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Summary for book '{book_id}' not found"
            )

        return {
            "status": "success",
            "message": f"Summary for book '{book_id}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting summary: {str(e)}"
        )
