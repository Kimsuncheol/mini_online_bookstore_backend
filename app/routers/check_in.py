"""
Check-In Router

Handles check-in related endpoints including:
- User check-in operations
- Check-in statistics retrieval
- Check-in profile and records
- Daily flag reset (for scheduled tasks)
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional
from app.models.check_in import CheckInResponse, CheckInStats, CheckInProfile
from app.services.check_in_service import get_check_in_service

router = APIRouter(prefix="/api/check-in", tags=["check-in"])


@router.post("/check-in", response_model=dict)
async def check_in(
    user_id: str = Query(..., description="The user ID"),
    user_email: str = Query(..., description="The user's email address"),
    user_name: str = Query(..., description="The user's name"),
):
    """
    Check in a user for today.

    Updates streak count, total check-ins, and determines earned coupons.

    Args:
        user_id (str): The unique identifier of the user
        user_email (str): The user's email address
        user_name (str): The user's name

    Returns:
        dict: Check-in response with updated statistics and earned coupons

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        service = get_check_in_service()
        result = service.create_or_update_check_in(user_id, user_email, user_name)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Check-in failed: {str(e)}"
        )


@router.get("/stats/{user_email}", response_model=dict)
async def get_check_in_stats(
    user_email: str = Path(..., description="The user's email address"),
):
    """
    Get check-in statistics for a user.

    Returns current streak, longest streak, total check-ins, and last check-in date.

    Args:
        user_email (str): The user's email address

    Returns:
        dict: User's check-in statistics

    Raises:
        HTTPException: 404 if user has no check-in data, 500 if database error occurs
    """
    try:
        service = get_check_in_service()
        stats = service.get_check_in_stats(user_email)

        if not stats:
            raise HTTPException(
                status_code=404,
                detail="User has no check-in data"
            )

        return {
            "success": True,
            "stats": stats.model_dump(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )


@router.get("/profile/{user_id}", response_model=dict)
async def get_user_check_in_profile(
    user_id: str = Path(..., description="The user ID"),
    user_email: str = Query(..., description="The user's email address"),
    user_name: str = Query(..., description="The user's name"),
):
    """
    Get complete check-in profile for a user.

    Returns comprehensive check-in data including statistics, recent records, and coupons.

    Args:
        user_id (str): The unique identifier of the user
        user_email (str): The user's email address
        user_name (str): The user's name

    Returns:
        dict: User's complete check-in profile

    Raises:
        HTTPException: 404 if user has no check-in data, 500 if database error occurs
    """
    try:
        service = get_check_in_service()
        profile = service.get_user_check_in_profile(user_id, user_email, user_name)

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="User has no check-in data"
            )

        return {
            "success": True,
            "profile": profile.model_dump(mode='json'),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch profile: {str(e)}"
        )


@router.get("/records/{user_email}", response_model=dict)
async def get_check_in_records(
    user_email: str = Path(..., description="The user's email address"),
    days: Optional[int] = Query(
        90,
        ge=1,
        le=365,
        description="Number of days to retrieve (default: 90)"
    ),
):
    """
    Get check-in records for a user.

    Returns daily check-in records for the specified number of days.

    Args:
        user_email (str): The user's email address
        days (Optional[int]): Number of days to retrieve (default: 90, max: 365)

    Returns:
        dict: List of check-in records

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        service = get_check_in_service()
        records = service.get_check_in_records(user_email, days=days or 90)

        return {
            "success": True,
            "records": [record.model_dump() for record in records],
            "count": len(records),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch records: {str(e)}"
        )


@router.post("/reset-daily-flags", response_model=dict)
async def reset_daily_check_in_flags():
    """
    Reset checked_in_today flag for all users.

    This endpoint should be called once per day via a scheduled task/cron job
    to reset the daily check-in flag for all users.

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        service = get_check_in_service()
        result = service.reset_daily_flags()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset flags: {str(e)}"
        )


__all__ = ["router"]
