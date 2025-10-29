"""
Author Router

Handles author profile operations including:
- Get author profile
- Get author by email
- Get all authors
- Get verified authors
- Update author profile
- Verify author
- Get author statistics
- Get author public profile
- Delete author account
"""

from fastapi import APIRouter, HTTPException, Path, Query, status
from typing import Optional
from app.models.author import Author, AuthorUpdate, AuthorProfile, AuthorStatistics
from app.services.author_service import get_author_service

router = APIRouter(prefix="/api/authors", tags=["authors"])


@router.get("/{author_id}", response_model=dict)
async def get_author_profile(author_id: str = Path(..., description="The author ID")):
    """
    Get an author's profile by their ID.

    Args:
        author_id (str): The unique identifier of the author

    Returns:
        dict: Author profile data

    Raises:
        HTTPException: 404 if author not found, 500 if database error occurs
    """
    try:
        author_service = get_author_service()
        author = author_service.fetch_author_by_id(author_id)

        if author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Author with ID '{author_id}' not found",
            )

        return author.model_dump(by_alias=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching author: {str(e)}",
        )


@router.get("/email/{email}", response_model=dict)
async def get_author_by_email(email: str = Path(..., description="The author's email address")):
    """
    Get an author's profile by their email address.

    Args:
        email (str): The email address of the author

    Returns:
        dict: Author profile data

    Raises:
        HTTPException: 404 if author not found, 500 if database error occurs
    """
    try:
        author_service = get_author_service()
        author = author_service.fetch_author_by_email(email)

        if author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Author with email '{email}' not found",
            )

        return author.model_dump(by_alias=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching author by email: {str(e)}",
        )


@router.get("", response_model=list)
async def get_all_authors(limit: Optional[int] = Query(None, ge=1, le=100)):
    """
    Get all authors (with optional limit).

    Args:
        limit (Optional[int]): Maximum number of authors to return

    Returns:
        list: List of all authors

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        author_service = get_author_service()
        authors = author_service.fetch_all_authors()

        # Apply limit if specified
        if limit:
            authors = authors[:limit]

        return [author.model_dump(by_alias=True) for author in authors]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching authors: {str(e)}",
        )


@router.get("/verified/list", response_model=list)
async def get_verified_authors(limit: Optional[int] = Query(None, ge=1, le=100)):
    """
    Get all verified authors (with optional limit).

    Args:
        limit (Optional[int]): Maximum number of verified authors to return

    Returns:
        list: List of verified authors

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        author_service = get_author_service()
        authors = author_service.fetch_verified_authors()

        # Apply limit if specified
        if limit:
            authors = authors[:limit]

        return [author.model_dump(by_alias=True) for author in authors]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching verified authors: {str(e)}",
        )


@router.patch("/{author_id}", response_model=dict)
async def update_author_profile(
    author_id: str = Path(..., description="The author ID"),
    update_data: AuthorUpdate = None,
):
    """
    Update an author's profile.

    Allows updating:
    - Display name
    - Bio and website
    - Social media links
    - Phone number
    - Address
    - Photo URL
    - Email
    - Preferences

    Args:
        author_id (str): The unique identifier of the author
        update_data (AuthorUpdate): The fields to update

    Returns:
        dict: Updated author profile data

    Raises:
        HTTPException:
            - 400 if no update data provided
            - 404 if author not found
            - 500 if database error occurs
    """
    try:
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Update data is required"
            )

        author_service = get_author_service()
        updated_author = author_service.update_author(author_id, update_data)

        if updated_author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Author with ID '{author_id}' not found",
            )

        return updated_author.model_dump(by_alias=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating author profile: {str(e)}",
        )


@router.post("/{author_id}/verify", response_model=dict)
async def verify_author(author_id: str = Path(..., description="The author ID")):
    """
    Verify an author and add verification badge.

    Args:
        author_id (str): The unique identifier of the author

    Returns:
        dict: Updated author profile data with verification

    Raises:
        HTTPException: 404 if author not found, 500 if database error occurs
    """
    try:
        author_service = get_author_service()
        updated_author = author_service.verify_author(author_id)

        if updated_author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Author with ID '{author_id}' not found",
            )

        return updated_author.model_dump(by_alias=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying author: {str(e)}",
        )


@router.get("/{author_id}/statistics", response_model=dict)
async def get_author_statistics(author_id: str = Path(..., description="The author ID")):
    """
    Get author statistics.

    Returns:
    - Total books published
    - Total readers reached
    - Average rating
    - Total reviews
    - Total followers

    Args:
        author_id (str): The unique identifier of the author

    Returns:
        dict: Author statistics

    Raises:
        HTTPException: 404 if author not found, 500 if database error occurs
    """
    try:
        author_service = get_author_service()
        stats = author_service.get_author_statistics(author_id)

        if stats is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Author with ID '{author_id}' not found",
            )

        return stats.model_dump(by_alias=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching author statistics: {str(e)}",
        )


@router.get("/{author_id}/public-profile", response_model=dict)
async def get_author_public_profile(author_id: str = Path(..., description="The author ID")):
    """
    Get author public profile (for public display on author page).

    Returns profile information suitable for public display:
    - Basic info (name, email, bio, website)
    - Verification status
    - Publishing statistics
    - Average rating

    Args:
        author_id (str): The unique identifier of the author

    Returns:
        dict: Author public profile data

    Raises:
        HTTPException: 404 if author not found, 500 if database error occurs
    """
    try:
        author_service = get_author_service()
        profile = author_service.get_author_profile(author_id)

        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Author with ID '{author_id}' not found",
            )

        return profile.model_dump(by_alias=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching author public profile: {str(e)}",
        )


@router.put("/{author_id}/statistics", response_model=dict)
async def update_author_statistics(
    author_id: str = Path(..., description="The author ID"),
    books_published: Optional[int] = Query(None, ge=0, description="Total books published"),
    readers_reached: Optional[int] = Query(None, ge=0, description="Total readers reached"),
    average_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Average rating"),
):
    """
    Update author statistics.

    Allows updating:
    - Total books published
    - Total readers reached
    - Average rating

    Args:
        author_id (str): The unique identifier of the author
        books_published (Optional[int]): Number of books published
        readers_reached (Optional[int]): Number of readers reached
        average_rating (Optional[float]): Average rating (0-5)

    Returns:
        dict: Updated author profile data with new statistics

    Raises:
        HTTPException: 404 if author not found, 500 if database error occurs
    """
    try:
        author_service = get_author_service()
        updated_author = author_service.update_author_statistics(
            author_id,
            books_published=books_published,
            readers_reached=readers_reached,
            average_rating=average_rating,
        )

        if updated_author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Author with ID '{author_id}' not found",
            )

        return updated_author.model_dump(by_alias=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating author statistics: {str(e)}",
        )


@router.delete("/{author_id}/account")
async def delete_author_account(author_id: str = Path(..., description="The author ID")):
    """
    Delete an author's account permanently.

    This will:
    1. Delete the author from the authors collection
    2. Remove all associated author data

    WARNING: This action is irreversible!

    Args:
        author_id (str): The unique identifier of the author to delete

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException:
            - 404 if author not found
            - 500 if database error occurs
    """
    try:
        author_service = get_author_service()

        # First check if author exists
        author = author_service.fetch_author_by_id(author_id)
        if author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Author with ID '{author_id}' not found",
            )

        # Delete the author
        success = author_service.delete_author(author_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete author account",
            )

        return {
            "status": "success",
            "message": f"Account for author '{author_id}' has been permanently deleted",
            "deleted_email": author.email,
            "deleted_name": author.display_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting author account: {str(e)}",
        )
