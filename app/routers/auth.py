"""
Auth Router

Handles authentication operations including:
- User sign-up
- User sign-out
- Session management
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from typing import Literal, Optional
from pydantic import AliasChoices, BaseModel, EmailStr, Field
from app.services.auth_service import get_auth_service
from app.models.member import UserPreferences
from app.models.oauth import (
    KakaoSignUpRequest,
    KakaoSignInRequest,
    KakaoAuthResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    """Request model for user sign-up."""

    email: EmailStr = Field(..., description="User's email address")
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User's display name/username",
        alias="displayName",
        validation_alias=AliasChoices("displayName", "display_name"),
        serialization_alias="displayName",
    )


class SignUpResponse(BaseModel):
    """Response model for successful sign-up aligned with the new User interface."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    display_name: Optional[str] = Field(
        None,
        description="User display name",
        alias="displayName",
        validation_alias=AliasChoices("displayName", "display_name"),
        serialization_alias="displayName",
    )
    photo_url: Optional[str] = Field(
        None,
        description="User profile photo URL",
        alias="photoURL",
        validation_alias=AliasChoices("photoURL", "photo_url"),
        serialization_alias="photoURL",
    )
    role: Literal["admin", "author", "user"] = Field(
        default="user", description="User role determining permissions"
    )
    is_email_verified: bool = Field(
        default=False,
        description="Email verification status",
        alias="isEmailVerified",
        validation_alias=AliasChoices("isEmailVerified", "is_email_verified"),
        serialization_alias="isEmailVerified",
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
        alias="createdAt",
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    last_sign_in_at: Optional[datetime] = Field(
        None,
        description="Last sign-in timestamp",
        alias="lastSignInAt",
        validation_alias=AliasChoices("lastSignInAt", "last_sign_in_at"),
        serialization_alias="lastSignInAt",
    )
    preferences: Optional[UserPreferences] = Field(
        None, description="User notification and marketing preferences"
    )
    phone: Optional[str] = Field(None, description="User phone number")
    address: Optional[str] = Field(None, description="User address")
    message: str = Field(..., description="Success message")

    class Config:
        """Allow population by field name."""

        populate_by_name = True


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
            display_name=member.display_name,
            photo_url=member.photo_url,
            role=member.role,
            is_email_verified=member.is_email_verified,
            created_at=member.created_at,
            last_sign_in_at=member.last_sign_in_at,
            preferences=member.preferences,
            phone=member.phone,
            address=member.address,
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


# ==================== KAKAO OAUTH ENDPOINTS ====================


@router.post(
    "/kakao/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=KakaoAuthResponse,
)
async def sign_up_with_kakao(request: KakaoSignUpRequest):
    """
    Sign up a new user using KakaoTalk OAuth.

    This endpoint handles the OAuth callback from KakaoTalk and creates a new user account
    if the email doesn't already exist.

    Args:
        request (KakaoSignUpRequest): OAuth code from KakaoTalk callback

    Returns:
        KakaoAuthResponse: User information and success message

    Raises:
        HTTPException:
            - 400 if KakaoTalk authentication fails or email verification fails
            - 500 if database error occurs
    """
    try:
        auth_service = get_auth_service()
        user, is_new = await auth_service.sign_up_with_kakao(
            kakao_code=request.code,
            display_name=request.display_name,
            redirect_uri=request.redirect_uri,
        )

        return KakaoAuthResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            photo_url=user.photo_url,
            kakao_id=user.kakao_id,
            is_new_user=is_new,
            message="User signed up successfully with KakaoTalk"
            if is_new
            else "User already exists, KakaoTalk account linked",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error signing up with KakaoTalk: {str(e)}",
        )


@router.post("/kakao/signin", response_model=KakaoAuthResponse)
async def sign_in_with_kakao(request: KakaoSignInRequest):
    """
    Sign in an existing user using KakaoTalk OAuth.

    This endpoint handles the OAuth callback from KakaoTalk and authenticates an existing user.

    Args:
        request (KakaoSignInRequest): OAuth code from KakaoTalk callback

    Returns:
        KakaoAuthResponse: User information and success message

    Raises:
        HTTPException:
            - 400 if KakaoTalk authentication fails or user not found
            - 500 if database error occurs
    """
    try:
        auth_service = get_auth_service()
        user = await auth_service.sign_in_with_kakao(
            kakao_code=request.code,
            redirect_uri=request.redirect_uri,
        )

        return KakaoAuthResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            photo_url=user.photo_url,
            kakao_id=user.kakao_id,
            is_new_user=False,
            message="User signed in successfully with KakaoTalk",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error signing in with KakaoTalk: {str(e)}",
        )
