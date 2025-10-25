"""
Auth Router

Handles authentication operations including:
- User sign-up
- User sign-out
- Session management
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from app.services.auth_service import get_auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    """Request model for user sign-up."""

    email: EmailStr = Field(..., description="User's email address")
    display_name: str = Field(
        ..., min_length=1, max_length=255, description="User's display name/username"
    )


class SignUpResponse(BaseModel):
    """Response model for successful sign-up."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    display_name: str = Field(..., description="User display name")
    message: str = Field(..., description="Success message")


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=SignUpResponse)
async def sign_up(request: SignUpRequest):
    """
    Sign up a new user.

    Creates a new member in the members collection with the provided email and username.

    Args:
        request (SignUpRequest): Sign-up request containing email and display_name

    Returns:
        SignUpResponse: User information and success message

    Raises:
        HTTPException:
            - 400 if email already exists
            - 500 if database error occurs
    """
    print("Here")
    try:
        auth_service = get_auth_service()
        member = await auth_service.sign_up_user(
            email=request.email, display_name=request.display_name
        )

        return SignUpResponse(
            id=member.id,
            email=member.email,
            display_name=member.display_name or "",
            message="User signed up successfully",
        )

    except ValueError as e:
        # Email already exists
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error signing up user: {str(e)}",
        )


@router.post("/signout")
async def sign_out(user_id: str):
    """
    Sign out a user.

    Invalidates the user's session and updates their sign-out status.

    Args:
        user_id (str): The ID of the user to sign out

    Returns:
        dict: Success message

    Raises:
        HTTPException:
            - 404 if user not found
            - 500 if database error occurs
    """
    try:
        auth_service = get_auth_service()
        success = await auth_service.sign_out_user(user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found",
            )

        return {"status": "success", "message": f"User '{user_id}' signed out successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error signing out user: {str(e)}",
        )


@router.get("/session/{user_id}")
async def get_session_info(user_id: str):
    """
    Get user session information.

    Args:
        user_id (str): The ID of the user

    Returns:
        dict: User session information

    Raises:
        HTTPException:
            - 404 if user not found
            - 500 if database error occurs
    """
    try:
        auth_service = get_auth_service()
        session_info = await auth_service.get_user_session_info(user_id)

        if session_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found",
            )

        return session_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting session info: {str(e)}",
        )


@router.get("/session/{user_id}/verify")
async def verify_session(user_id: str):
    """
    Verify if a user has an active session.

    Args:
        user_id (str): The ID of the user

    Returns:
        dict: Session verification result

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        auth_service = get_auth_service()
        is_active = await auth_service.verify_user_session(user_id)

        return {
            "user_id": user_id,
            "is_active": is_active,
            "message": "Session is active" if is_active else "Session is not active",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying session: {str(e)}",
        )
