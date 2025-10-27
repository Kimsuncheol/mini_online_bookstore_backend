"""
Advertisements Router

Handles advertisement-related operations including:
- CRUD operations for advertisements
- Fetching active advertisements for hero carousel
- Managing advertisement status and order
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional
from app.models.advertisement import (
    Advertisement,
    AdvertisementCreate,
    AdvertisementUpdate,
    HeroCarouselBook,
)
from app.services.advertisement_service import get_advertisement_service

router = APIRouter(prefix="/api/advertisements", tags=["advertisements"])


# ==================== ADVERTISEMENT CRUD ENDPOINTS ====================


@router.post("", status_code=201)
async def create_advertisement(ad_data: AdvertisementCreate):
    """
    Create a new advertisement for the hero carousel.

    Args:
        ad_data (AdvertisementCreate): The advertisement data to create

    Returns:
        Advertisement: The created advertisement with ID

    Raises:
        HTTPException: 400 if invalid data, 500 if database error occurs
    """
    try:
        ad_service = get_advertisement_service()
        advertisement = ad_service.create_advertisement(ad_data)
        return advertisement.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating advertisement: {str(e)}")


@router.get("/{ad_id}")
async def get_advertisement(ad_id: str = Path(..., description="The advertisement ID")):
    """
    Fetch an advertisement by its ID.

    Args:
        ad_id (str): The unique identifier of the advertisement

    Returns:
        Advertisement: The advertisement data

    Raises:
        HTTPException: 404 if advertisement not found, 500 if database error occurs
    """
    try:
        ad_service = get_advertisement_service()
        advertisement = ad_service.get_advertisement_by_id(ad_id)

        if advertisement is None:
            raise HTTPException(
                status_code=404, detail=f"Advertisement with ID '{ad_id}' not found"
            )

        return advertisement.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching advertisement: {str(e)}")


@router.get("")
async def get_all_advertisements(limit: Optional[int] = Query(None, ge=1, le=100)):
    """
    Fetch all advertisements from the bookstore.

    Args:
        limit (Optional[int]): Maximum number of advertisements to return

    Returns:
        list: List of all advertisements

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        ad_service = get_advertisement_service()
        advertisements = ad_service.get_all_advertisements(limit=limit)
        return [ad.model_dump() for ad in advertisements]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching advertisements: {str(e)}")


@router.patch("/{ad_id}")
async def update_advertisement(
    ad_id: str = Path(..., description="The advertisement ID"),
    update_data: AdvertisementUpdate = None,
):
    """
    Update an existing advertisement.

    Args:
        ad_id (str): The ID of the advertisement to update
        update_data (AdvertisementUpdate): The data to update

    Returns:
        Advertisement: The updated advertisement

    Raises:
        HTTPException: 400 if invalid data, 404 if not found, 500 if database error occurs
    """
    try:
        if not update_data:
            raise HTTPException(status_code=400, detail="Update data is required")

        ad_service = get_advertisement_service()
        updated_ad = ad_service.update_advertisement(ad_id, update_data)

        if updated_ad is None:
            raise HTTPException(
                status_code=404, detail=f"Advertisement with ID '{ad_id}' not found"
            )

        return updated_ad.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating advertisement: {str(e)}")


@router.delete("/{ad_id}")
async def delete_advertisement(ad_id: str = Path(..., description="The advertisement ID")):
    """
    Delete an advertisement from the bookstore.

    Args:
        ad_id (str): The ID of the advertisement to delete

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: 404 if not found, 500 if database error occurs
    """
    try:
        ad_service = get_advertisement_service()
        success = ad_service.delete_advertisement(ad_id)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Advertisement with ID '{ad_id}' not found"
            )

        return {
            "status": "success",
            "message": f"Advertisement '{ad_id}' deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting advertisement: {str(e)}")


# ==================== HERO CAROUSEL ENDPOINTS ====================


@router.get("/active/list")
async def get_active_advertisements(limit: Optional[int] = Query(10, ge=1, le=100)):
    """
    Fetch active advertisements (for admin/management).

    Args:
        limit (Optional[int]): Maximum number of advertisements to return (default: 10)

    Returns:
        list: List of active advertisements

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        ad_service = get_advertisement_service()
        advertisements = ad_service.get_active_advertisements(limit=limit)
        return [ad.model_dump() for ad in advertisements]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching active advertisements: {str(e)}"
        )


@router.get("/hero-carousel/books")
async def get_hero_carousel_books(limit: Optional[int] = Query(10, ge=1, le=100)):
    """
    Fetch hero carousel books (client-facing endpoint).

    Returns books in the format expected by the Next.js client
    (HeroCarouselBook interface).

    Args:
        limit (Optional[int]): Maximum number of books to return (default: 10)

    Returns:
        list: List of hero carousel books

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        ad_service = get_advertisement_service()
        carousel_books = ad_service.get_hero_carousel_books(limit=limit)
        return [book.model_dump(by_alias=True) for book in carousel_books]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching hero carousel books: {str(e)}"
        )


# ==================== MANAGEMENT ENDPOINTS ====================


@router.patch("/{ad_id}/toggle-active")
async def toggle_advertisement_status(ad_id: str = Path(..., description="The advertisement ID")):
    """
    Toggle the active status of an advertisement.

    Args:
        ad_id (str): The ID of the advertisement

    Returns:
        Advertisement: The updated advertisement

    Raises:
        HTTPException: 404 if not found, 500 if database error occurs
    """
    try:
        ad_service = get_advertisement_service()
        updated_ad = ad_service.toggle_active_status(ad_id)

        if updated_ad is None:
            raise HTTPException(
                status_code=404, detail=f"Advertisement with ID '{ad_id}' not found"
            )

        return updated_ad.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error toggling advertisement status: {str(e)}"
        )


@router.patch("/{ad_id}/reorder")
async def reorder_advertisement(
    ad_id: str = Path(..., description="The advertisement ID"),
    new_order: int = Query(..., ge=0, description="New display order"),
):
    """
    Change the display order of an advertisement.

    Args:
        ad_id (str): The ID of the advertisement
        new_order (int): The new display order (0 = first)

    Returns:
        Advertisement: The updated advertisement

    Raises:
        HTTPException: 404 if not found, 500 if database error occurs
    """
    try:
        ad_service = get_advertisement_service()
        updated_ad = ad_service.reorder_advertisements(ad_id, new_order)

        if updated_ad is None:
            raise HTTPException(
                status_code=404, detail=f"Advertisement with ID '{ad_id}' not found"
            )

        return updated_ad.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reordering advertisement: {str(e)}"
        )
