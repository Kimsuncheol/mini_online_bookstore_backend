"""
Like Router

Handles like-related operations including:
- Adding/removing likes
- Fetching user's liked books
- Checking like status
- Getting like counts
- Toggling likes
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional
from app.models.like import (
    Like,
    LikeCreate,
    LikeResponse,
    LikeStatusResponse,
    LikeCountResponse,
)
from app.services.like_service import get_like_service

router = APIRouter(prefix="/api/likes", tags=["likes"])


# ==================== LIKE CRUD ENDPOINTS ====================


@router.post("", status_code=201)
async def add_like(like_data: LikeCreate):
    """
    Add a book to user's liked books.

    Args:
        like_data (LikeCreate): The like data to create

    Returns:
        LikeResponse: The created like information

    Raises:
        HTTPException: 400 if book is already liked, 500 if database error occurs
    """
    try:
        like_service = get_like_service()
        like = like_service.create_like(like_data)

        # Convert to client-facing format
        response = like_service.like_to_response(like)
        return response.model_dump(by_alias=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding like: {str(e)}")


@router.delete("/{like_id}")
async def remove_like(like_id: str = Path(..., description="The like ID")):
    """
    Remove a like from user's liked books.

    Args:
        like_id (str): The ID of the like to remove

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: 404 if like not found, 500 if database error occurs
    """
    try:
        like_service = get_like_service()
        success = like_service.remove_like(like_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Like with ID '{like_id}' not found")

        return {"status": "success", "message": f"Like '{like_id}' removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing like: {str(e)}")


@router.delete("/book/{book_id}/user/{user_email}")
async def remove_like_by_book_and_user(
    book_id: str = Path(..., description="The book ID"),
    user_email: str = Path(..., description="The user email"),
):
    """
    Remove a like by book ID and user email.

    Args:
        book_id (str): The ID of the book
        user_email (str): The user's email address

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: 404 if like not found, 500 if database error occurs
    """
    try:
        like_service = get_like_service()
        success = like_service.remove_like_by_book_and_user(book_id, user_email)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Like for book '{book_id}' by user '{user_email}' not found",
            )

        return {
            "status": "success",
            "message": f"Book '{book_id}' removed from user's likes",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing like: {str(e)}")


# ==================== USER LIKES ENDPOINTS ====================


@router.get("/user/{user_email}")
async def get_user_likes(
    user_email: str = Path(..., description="The user email"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of likes to return"),
):
    """
    Fetch all liked books for a user.

    Args:
        user_email (str): The user's email address
        limit (Optional[int]): Maximum number of likes to return

    Returns:
        list: List of user's liked books in client format

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        like_service = get_like_service()
        likes = like_service.get_user_likes(user_email, limit=limit)

        # Convert to client-facing format
        return [like_service.like_to_response(like).model_dump(by_alias=True) for like in likes]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching user's likes: {str(e)}"
        )


@router.get("/user/{user_email}/count")
async def get_user_like_count(user_email: str = Path(..., description="The user email")):
    """
    Get the total number of books liked by a user.

    Args:
        user_email (str): The user's email address

    Returns:
        dict: Object containing user email and like count

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        like_service = get_like_service()
        count = like_service.get_user_like_count(user_email)
        return {"user_email": user_email, "like_count": count}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error counting user's likes: {str(e)}"
        )


# ==================== BOOK LIKES ENDPOINTS ====================


@router.get("/book/{book_id}")
async def get_book_likes(
    book_id: str = Path(..., description="The book ID"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of likes to return"),
):
    """
    Fetch all likes for a specific book.

    Args:
        book_id (str): The ID of the book
        limit (Optional[int]): Maximum number of likes to return

    Returns:
        list: List of likes for the book

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        like_service = get_like_service()
        likes = like_service.get_book_likes(book_id, limit=limit)
        return [like.model_dump() for like in likes]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching book likes: {str(e)}"
        )


@router.get("/book/{book_id}/count")
async def get_book_like_count(book_id: str = Path(..., description="The book ID")):
    """
    Get the total number of likes for a book.

    Args:
        book_id (str): The ID of the book

    Returns:
        LikeCountResponse: Object containing book ID and like count

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        like_service = get_like_service()
        result = like_service.get_book_like_count(book_id)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error counting book likes: {str(e)}"
        )


# ==================== LIKE STATUS ENDPOINT ====================


@router.get("/book/{book_id}/user/{user_email}/status")
async def check_like_status(
    book_id: str = Path(..., description="The book ID"),
    user_email: str = Path(..., description="The user email"),
):
    """
    Check if a book is liked by a user.

    Args:
        book_id (str): The ID of the book
        user_email (str): The user's email address

    Returns:
        LikeStatusResponse: Object containing like status and like ID

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        like_service = get_like_service()
        result = like_service.is_book_liked_by_user(book_id, user_email)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking like status: {str(e)}"
        )


# ==================== TOGGLE LIKE ENDPOINT ====================


@router.post("/toggle")
async def toggle_like(like_data: LikeCreate):
    """
    Toggle like status (add if not liked, remove if liked).

    Convenient endpoint that automatically adds or removes a like based on current status.

    Args:
        like_data (LikeCreate): The like data

    Returns:
        dict: Object containing action taken ('added' or 'removed'), message, and status

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        like_service = get_like_service()
        result = like_service.toggle_like(like_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling like: {str(e)}")


# ==================== GET LIKE BY ID ====================


@router.get("/{like_id}")
async def get_like(like_id: str = Path(..., description="The like ID")):
    """
    Fetch a like by its ID.

    Args:
        like_id (str): The unique identifier of the like

    Returns:
        Like: The like data

    Raises:
        HTTPException: 404 if like not found, 500 if database error occurs
    """
    try:
        like_service = get_like_service()
        like = like_service.get_like_by_id(like_id)

        if like is None:
            raise HTTPException(status_code=404, detail=f"Like with ID '{like_id}' not found")

        return like.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching like: {str(e)}")
