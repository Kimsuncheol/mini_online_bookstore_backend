"""
Coupon Router

Handles coupon-related endpoints including:
- Coupon creation, retrieval, update, deletion
- Coupon usage tracking
- Coupon issuance for milestones
- Coupon issue records management
"""

from fastapi import APIRouter, HTTPException, Path, Query, Body
from typing import Optional
from app.models.coupon import CouponCreate, CouponUpdate
from app.services.coupon_service import get_coupon_service

router = APIRouter(prefix="/api/coupons", tags=["coupons"])


# ==================== COUPON CRUD ENDPOINTS ====================


@router.post("", status_code=201, response_model=dict)
async def create_coupon(
    user_id: str = Query(..., description="The user ID"),
    user_email: str = Query(..., description="The user's email address"),
    coupon_data: CouponCreate = Body(...),
):
    """
    Create a new coupon for a user.

    Args:
        user_id (str): The unique identifier of the user
        user_email (str): The user's email address
        coupon_data (CouponCreate): Coupon data (code, discount_value, source, description)

    Returns:
        dict: Created coupon details

    Raises:
        HTTPException:
            - 400 if no coupon data provided
            - 500 if database error occurs
    """
    try:
        if not coupon_data:
            raise HTTPException(
                status_code=400,
                detail="No coupon data provided"
            )

        service = get_coupon_service()
        coupon = service.create_coupon(user_id, user_email, coupon_data)

        return {
            "success": True,
            "message": "Coupon created successfully",
            "coupon": coupon.model_dump(mode='json'),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create coupon: {str(e)}"
        )


@router.get("", response_model=dict)
async def get_user_coupons(
    user_email: str = Query(..., description="The user's email address"),
    active_only: Optional[bool] = Query(
        False,
        description="Return only active (unused and non-expired) coupons"
    ),
):
    """
    Get all coupons for a user.

    Args:
        user_email (str): The user's email address
        active_only (Optional[bool]): If True, return only active coupons (default: False)

    Returns:
        dict: List of user's coupons and count

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        service = get_coupon_service()
        result = service.get_user_coupons(user_email, active_only=active_only or False)

        return {
            "success": True,
            "coupons": [c.model_dump(mode='json') for c in result["coupons"]],
            "count": result["count"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch coupons: {str(e)}"
        )


@router.get("/{coupon_id}", response_model=dict)
async def get_coupon(
    coupon_id: str = Path(..., description="The coupon ID"),
    user_email: str = Query(..., description="The user's email address"),
):
    """
    Get a coupon by ID.

    Args:
        coupon_id (str): The unique identifier of the coupon
        user_email (str): The user's email address

    Returns:
        dict: Coupon details

    Raises:
        HTTPException: 404 if coupon not found, 500 if database error occurs
    """
    try:
        service = get_coupon_service()
        coupon = service.get_coupon(coupon_id, user_email)

        if not coupon:
            raise HTTPException(
                status_code=404,
                detail="Coupon not found"
            )

        return {
            "success": True,
            "coupon": coupon.model_dump(mode='json'),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch coupon: {str(e)}"
        )


@router.patch("/{coupon_id}", response_model=dict)
async def update_coupon(
    coupon_id: str = Path(..., description="The coupon ID"),
    user_email: str = Query(..., description="The user's email address"),
    update_data: CouponUpdate = Body(...),
):
    """
    Update a coupon.

    Args:
        coupon_id (str): The unique identifier of the coupon
        user_email (str): The user's email address
        update_data (CouponUpdate): Fields to update

    Returns:
        dict: Updated coupon details

    Raises:
        HTTPException:
            - 400 if no update data provided
            - 404 if coupon not found
            - 500 if database error occurs
    """
    try:
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No update data provided"
            )

        service = get_coupon_service()
        coupon = service.update_coupon(coupon_id, user_email, update_data)

        return {
            "success": True,
            "message": "Coupon updated successfully",
            "coupon": coupon.model_dump(mode='json'),
        }
    except HTTPException:
        raise
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update coupon: {str(e)}"
        )


@router.delete("/{coupon_id}", response_model=dict)
async def delete_coupon(
    coupon_id: str = Path(..., description="The coupon ID"),
    user_email: str = Query(..., description="The user's email address"),
):
    """
    Delete a coupon.

    Args:
        coupon_id (str): The unique identifier of the coupon
        user_email (str): The user's email address

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        service = get_coupon_service()
        result = service.delete_coupon(coupon_id, user_email)

        return {
            "success": True,
            "message": result["message"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete coupon: {str(e)}"
        )


# ==================== COUPON USAGE ENDPOINTS ====================


@router.post("/{coupon_id}/use", response_model=dict)
async def use_coupon(
    coupon_id: str = Path(..., description="The coupon ID"),
    user_email: str = Query(..., description="The user's email address"),
):
    """
    Mark a coupon as used.

    Args:
        coupon_id (str): The unique identifier of the coupon
        user_email (str): The user's email address

    Returns:
        dict: Updated coupon with used status

    Raises:
        HTTPException:
            - 404 if coupon not found
            - 500 if coupon already used, expired, or database error occurs
    """
    try:
        service = get_coupon_service()
        coupon = service.use_coupon(coupon_id, user_email)

        return {
            "success": True,
            "message": "Coupon used successfully",
            "coupon": coupon.model_dump(mode='json'),
        }
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to use coupon: {error_msg}"
        )


@router.post("/{coupon_id}/issue", response_model=dict)
async def issue_coupon(
    coupon_id: str = Path(..., description="The coupon ID"),
    user_id: str = Query(..., description="The user ID"),
    user_email: str = Query(..., description="The user's email address"),
):
    """
    Mark a coupon as issued.

    Args:
        coupon_id (str): The unique identifier of the coupon
        user_id (str): The unique identifier of the user
        user_email (str): The user's email address

    Returns:
        dict: Updated coupon with issued status

    Raises:
        HTTPException: 404 if coupon not found, 500 if database error occurs
    """
    try:
        service = get_coupon_service()
        coupon = service.issue_coupon(coupon_id, user_id, user_email)

        return {
            "success": True,
            "message": "Coupon issued successfully",
            "coupon": coupon.model_dump(mode='json'),
        }
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to issue coupon: {error_msg}"
        )


# ==================== COUPON ISSUE RECORD ENDPOINTS ====================


@router.post("/issue-records", status_code=201, response_model=dict)
async def create_coupon_issue_record(
    user_id: str = Query(..., description="The user ID"),
    user_email: str = Query(..., description="The user's email address"),
    streak_days: int = Query(..., ge=7, description="Streak days (7, 14, 30, etc)"),
    coupon_value: float = Query(..., gt=0, description="Coupon value in dollars"),
):
    """
    Create a coupon issue record for a streak milestone.

    Called when a user reaches a streak milestone (7, 14, 30 days, etc).

    Args:
        user_id (str): The unique identifier of the user
        user_email (str): The user's email address
        streak_days (int): Number of consecutive days (e.g., 7, 14, 30)
        coupon_value (float): Dollar value of the coupon

    Returns:
        dict: Created coupon issue record

    Raises:
        HTTPException: 500 if database error occurs or coupon already issued
    """
    try:
        service = get_coupon_service()
        record = service.create_coupon_issue_record(
            user_id, user_email, streak_days, coupon_value
        )

        return {
            "success": True,
            "message": "Coupon issue record created successfully",
            "record": record.model_dump(mode='json'),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create coupon issue record: {str(e)}"
        )


@router.get("/issue-records/{user_email}", response_model=dict)
async def get_coupon_issue_records(
    user_email: str = Path(..., description="The user's email address"),
):
    """
    Get all coupon issue records for a user.

    Shows which streak milestones have had coupons issued.

    Args:
        user_email (str): The user's email address

    Returns:
        dict: List of coupon issue records

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        service = get_coupon_service()
        records = service.get_coupon_issue_records(user_email)

        return {
            "success": True,
            "records": [r.model_dump(mode='json') for r in records],
            "count": len(records),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch coupon issue records: {str(e)}"
        )


__all__ = ["router"]
