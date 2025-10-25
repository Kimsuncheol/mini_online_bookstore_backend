"""
Member Router

Handles member/user profile operations including:
- Get member profile
- Get member by email
- Get all members
- Update member profile
- Delete account
"""

from fastapi import APIRouter, HTTPException, Path, Query, status
from typing import Optional
from app.models.member import Member, MemberUpdate
from app.services.member_service import get_member_service

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("/{member_id}", response_model=dict)
async def get_member_profile(member_id: str = Path(..., description="The member ID")):
    """
    Get a member's profile by their ID.

    Args:
        member_id (str): The unique identifier of the member

    Returns:
        dict: Member profile data

    Raises:
        HTTPException: 404 if member not found, 500 if database error occurs
    """
    try:
        member_service = get_member_service()
        member = member_service.fetch_user_by_id(member_id)

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member with ID '{member_id}' not found",
            )

        return member.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching member: {str(e)}",
        )


@router.get("/email/{email}", response_model=dict)
async def get_member_by_email(email: str = Path(..., description="The member's email address")):
    """
    Get a member's profile by their email address.

    Args:
        email (str): The email address of the member

    Returns:
        dict: Member profile data

    Raises:
        HTTPException: 404 if member not found, 500 if database error occurs
    """
    try:
        member_service = get_member_service()
        member = member_service.fetch_user_by_email(email)

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member with email '{email}' not found",
            )

        return member.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching member by email: {str(e)}",
        )


@router.get("", response_model=list)
async def get_all_members(limit: Optional[int] = Query(None, ge=1, le=100)):
    """
    Get all members (with optional limit).

    Args:
        limit (Optional[int]): Maximum number of members to return

    Returns:
        list: List of all members

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        member_service = get_member_service()
        members = member_service.fetch_all_users()

        # Apply limit if specified
        if limit:
            members = members[:limit]

        return [member.model_dump() for member in members]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching members: {str(e)}",
        )


@router.patch("/{member_id}", response_model=dict)
async def update_member_profile(
    member_id: str = Path(..., description="The member ID"),
    update_data: MemberUpdate = None,
):
    """
    Update a member's profile.

    Allows updating:
    - Display name
    - Phone number
    - Address
    - Photo URL
    - Email
    - Preferences (email notifications, marketing emails)

    Args:
        member_id (str): The unique identifier of the member
        update_data (MemberUpdate): The fields to update

    Returns:
        dict: Updated member profile data

    Raises:
        HTTPException:
            - 400 if no update data provided
            - 404 if member not found
            - 500 if database error occurs
    """
    try:
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Update data is required"
            )

        member_service = get_member_service()
        updated_member = member_service.update_user(member_id, update_data)

        if updated_member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member with ID '{member_id}' not found",
            )

        return updated_member.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating member profile: {str(e)}",
        )


@router.delete("/{member_id}/account")
async def delete_account(member_id: str = Path(..., description="The member ID")):
    """
    Delete a member's account permanently.

    This will:
    1. Delete the member from the members collection
    2. Remove all associated user data

    WARNING: This action is irreversible!

    Args:
        member_id (str): The unique identifier of the member to delete

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException:
            - 404 if member not found
            - 500 if database error occurs
    """
    try:
        member_service = get_member_service()

        # First check if member exists
        member = member_service.fetch_user_by_id(member_id)
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member with ID '{member_id}' not found",
            )

        # Delete the member
        success = member_service.delete_user(member_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete member account",
            )

        return {
            "status": "success",
            "message": f"Account for member '{member_id}' has been permanently deleted",
            "deleted_email": member.email,
            "deleted_name": member.display_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting account: {str(e)}",
        )


@router.get("/{member_id}/profile")
async def get_member_profile_detailed(member_id: str = Path(..., description="The member ID")):
    """
    Get detailed member profile information.

    Returns comprehensive profile data including:
    - Basic info (email, name, phone, address)
    - Account status (email verified, sign-in times)
    - Preferences (notifications settings)

    Args:
        member_id (str): The unique identifier of the member

    Returns:
        dict: Detailed member profile data

    Raises:
        HTTPException: 404 if member not found, 500 if database error occurs
    """
    try:
        member_service = get_member_service()
        member = member_service.fetch_user_by_id(member_id)

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member with ID '{member_id}' not found",
            )

        # Return detailed profile
        profile_data = member.model_dump()
        profile_data["profile_complete"] = all(
            [
                member.display_name,
                member.phone,
                member.address,
            ]
        )

        return profile_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching member profile: {str(e)}",
        )
