"""
OAuth Models

Defines Pydantic models for OAuth authentication flows including KakaoTalk OAuth.
Includes request/response models for OAuth token exchange and user information retrieval.
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, AliasChoices


# ==================== KAKAO OAUTH MODELS ====================


class KakaoTokenRequest(BaseModel):
    """Request model for exchanging KakaoTalk authorization code for access token."""

    code: str = Field(..., description="Authorization code from KakaoTalk OAuth callback")
    redirect_uri: Optional[str] = Field(
        None,
        description="Redirect URI used in the OAuth request (must match registered URI)",
        alias="redirectUri",
        validation_alias=AliasChoices("redirectUri", "redirect_uri"),
    )

    class Config:
        """Allow population by field name."""
        populate_by_name = True


class KakaoTokenResponse(BaseModel):
    """Response model containing KakaoTalk access token and related info."""

    access_token: str = Field(..., description="Access token for KakaoTalk API calls")
    token_type: str = Field(default="bearer", description="Token type (typically 'bearer')")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    refresh_token: Optional[str] = Field(
        None, description="Refresh token for obtaining new access token"
    )
    refresh_token_expires_in: Optional[int] = Field(
        None, description="Refresh token expiration time in seconds"
    )
    scope: Optional[str] = Field(
        None, description="Granted OAuth scopes (space-separated)"
    )

    class Config:
        """Allow population by field name."""
        populate_by_name = True


class KakaoUserProperties(BaseModel):
    """KakaoTalk user properties from OAuth."""

    nickname: Optional[str] = Field(None, description="KakaoTalk nickname")
    profile_image: Optional[str] = Field(
        None,
        description="KakaoTalk profile image URL",
        alias="profile_image",
    )
    thumbnail_image: Optional[str] = Field(
        None,
        description="KakaoTalk thumbnail image URL",
        alias="thumbnail_image",
    )

    class Config:
        """Allow population by field name."""
        populate_by_name = True


class KakaoAccount(BaseModel):
    """KakaoTalk account information from OAuth."""

    profile_needs_agreement: Optional[bool] = Field(
        None,
        description="Whether profile information requires additional agreement",
        alias="profile_needs_agreement",
    )
    profile: Optional[KakaoUserProperties] = Field(
        None, description="User profile information"
    )
    email_needs_agreement: Optional[bool] = Field(
        None,
        description="Whether email information requires additional agreement",
        alias="email_needs_agreement",
    )
    is_email_valid: Optional[bool] = Field(
        None,
        description="Whether email is verified",
        alias="is_email_valid",
    )
    is_email_verified: Optional[bool] = Field(
        None,
        description="Whether email is verified by the user",
        alias="is_email_verified",
    )
    email: Optional[str] = Field(None, description="User email address")
    has_phone_number: Optional[bool] = Field(
        None,
        description="Whether user has phone number",
        alias="has_phone_number",
    )
    phone_number: Optional[str] = Field(
        None,
        description="User phone number",
        alias="phone_number",
    )

    class Config:
        """Allow population by field name."""
        populate_by_name = True


class KakaoUserInfo(BaseModel):
    """User information retrieved from KakaoTalk OAuth."""

    id: int = Field(..., description="Unique KakaoTalk user ID")
    connected_at: str = Field(
        ...,
        description="Timestamp when account was connected (ISO 8601 format)",
        alias="connected_at",
    )
    properties: Optional[KakaoUserProperties] = Field(
        None, description="User properties"
    )
    kakao_account: Optional[KakaoAccount] = Field(
        None,
        description="KakaoTalk account information",
        alias="kakao_account",
    )

    class Config:
        """Allow population by field name."""
        populate_by_name = True


# ==================== AUTH OAUTH RESPONSE MODELS ====================


class KakaoSignUpRequest(BaseModel):
    """Request model for signing up with KakaoTalk OAuth."""

    code: str = Field(..., description="Authorization code from KakaoTalk OAuth callback")
    redirect_uri: Optional[str] = Field(
        None,
        description="Redirect URI used in the OAuth request",
        alias="redirectUri",
        validation_alias=AliasChoices("redirectUri", "redirect_uri"),
    )
    display_name: Optional[str] = Field(
        None,
        description="Optional custom display name (defaults to KakaoTalk nickname)",
        alias="displayName",
        validation_alias=AliasChoices("displayName", "display_name"),
    )

    class Config:
        """Allow population by field name."""
        populate_by_name = True


class KakaoSignInRequest(BaseModel):
    """Request model for signing in with KakaoTalk OAuth."""

    code: str = Field(..., description="Authorization code from KakaoTalk OAuth callback")
    redirect_uri: Optional[str] = Field(
        None,
        description="Redirect URI used in the OAuth request",
        alias="redirectUri",
        validation_alias=AliasChoices("redirectUri", "redirect_uri"),
    )

    class Config:
        """Allow population by field name."""
        populate_by_name = True


class KakaoAuthResponse(BaseModel):
    """Response model for KakaoTalk OAuth authentication (sign-in or sign-up)."""

    id: str = Field(..., description="User ID from the bookstore system")
    email: str = Field(..., description="User email address")
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
    kakao_id: Optional[str] = Field(
        None,
        description="KakaoTalk user ID",
        alias="kakaoId",
        validation_alias=AliasChoices("kakaoId", "kakao_id"),
        serialization_alias="kakaoId",
    )
    is_new_user: bool = Field(
        ...,
        description="Whether this is a new user account (sign-up) or existing (sign-in)",
        alias="isNewUser",
        validation_alias=AliasChoices("isNewUser", "is_new_user"),
        serialization_alias="isNewUser",
    )
    message: str = Field(
        ...,
        description="Success message indicating sign-in or sign-up",
    )

    class Config:
        """Allow population by field name."""
        populate_by_name = True


class OAuthErrorResponse(BaseModel):
    """Response model for OAuth errors."""

    error: str = Field(..., description="Error type/code")
    error_description: Optional[str] = Field(
        None,
        description="Detailed error description",
        alias="errorDescription",
        validation_alias=AliasChoices("errorDescription", "error_description"),
        serialization_alias="errorDescription",
    )
    error_uri: Optional[str] = Field(
        None,
        description="URI with more information about the error",
        alias="errorUri",
        validation_alias=AliasChoices("errorUri", "error_uri"),
        serialization_alias="errorUri",
    )

    class Config:
        """Allow population by field name."""
        populate_by_name = True


__all__ = [
    "KakaoTokenRequest",
    "KakaoTokenResponse",
    "KakaoUserProperties",
    "KakaoAccount",
    "KakaoUserInfo",
    "KakaoSignUpRequest",
    "KakaoSignInRequest",
    "KakaoAuthResponse",
    "OAuthErrorResponse",
]
