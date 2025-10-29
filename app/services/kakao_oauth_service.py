"""
KakaoTalk OAuth Service

Provides OAuth integration with KakaoTalk for user authentication.
Handles token exchange, user information retrieval, and account linking.
"""

import os
from typing import Optional, Any, Dict
from datetime import datetime
import aiohttp

from app.models.oauth import (
    KakaoTokenResponse,
    KakaoUserInfo,
    KakaoTokenRequest,
)


class KakaoOAuthService:
    """Service class for KakaoTalk OAuth operations."""

    # KakaoTalk OAuth endpoints
    KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

    def __init__(self):
        """Initialize KakaoTalk OAuth service with credentials from environment."""
        self.client_id = os.getenv("KAKAO_CLIENT_ID")
        self.client_secret = os.getenv("KAKAO_CLIENT_SECRET")
        self.redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:3000/auth/kakao/callback")

        if not self.client_id:
            raise ValueError("KAKAO_CLIENT_ID environment variable is not set")
        if not self.client_secret:
            raise ValueError("KAKAO_CLIENT_SECRET environment variable is not set")

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> KakaoTokenResponse:
        """
        Exchange authorization code for access token.

        This implements the OAuth 2.0 authorization code flow.

        Args:
            code: Authorization code from KakaoTalk OAuth callback
            redirect_uri: Optional override of default redirect URI (must match registered URI)

        Returns:
            KakaoTokenResponse: Access token and related information

        Raises:
            ValueError: If code is invalid or exchange fails
            Exception: If network request fails
        """
        uri = redirect_uri or self.redirect_uri

        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": uri,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.KAKAO_TOKEN_URL,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    data = await response.json()

                    if response.status != 200:
                        error = data.get("error", "Unknown error")
                        error_description = data.get("error_description", "")
                        raise ValueError(
                            f"KakaoTalk token exchange failed: {error} - {error_description}"
                        )

                    return KakaoTokenResponse(
                        access_token=data.get("access_token"),
                        token_type=data.get("token_type", "bearer"),
                        expires_in=data.get("expires_in"),
                        refresh_token=data.get("refresh_token"),
                        refresh_token_expires_in=data.get("refresh_token_expires_in"),
                        scope=data.get("scope"),
                    )

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Error exchanging KakaoTalk authorization code: {str(e)}")

    async def get_user_info(self, access_token: str) -> KakaoUserInfo:
        """
        Retrieve user information from KakaoTalk using access token.

        Args:
            access_token: KakaoTalk access token from token exchange

        Returns:
            KakaoUserInfo: User information including ID, email, and profile

        Raises:
            ValueError: If access token is invalid
            Exception: If network request fails
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.KAKAO_USER_INFO_URL,
                    headers=headers,
                ) as response:
                    data = await response.json()

                    if response.status != 200:
                        error = data.get("error", "Unknown error")
                        error_description = data.get("error_description", "")
                        raise ValueError(
                            f"KakaoTalk user info retrieval failed: {error} - {error_description}"
                        )

                    return KakaoUserInfo(**data)

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Error retrieving KakaoTalk user info: {str(e)}")

    async def get_user_email(self, access_token: str) -> Optional[str]:
        """
        Extract email from KakaoTalk user information.

        Args:
            access_token: KakaoTalk access token

        Returns:
            Optional[str]: User email if available and verified, None otherwise
        """
        try:
            user_info = await self.get_user_info(access_token)

            # Check if email is available and verified
            if user_info.kakao_account and user_info.kakao_account.email:
                if user_info.kakao_account.is_email_verified:
                    return user_info.kakao_account.email

            return None

        except Exception as e:
            print(f"Warning: Error extracting email from KakaoTalk: {str(e)}")
            return None

    async def get_user_nickname(self, access_token: str) -> Optional[str]:
        """
        Extract nickname from KakaoTalk user information.

        Args:
            access_token: KakaoTalk access token

        Returns:
            Optional[str]: User nickname if available, None otherwise
        """
        try:
            user_info = await self.get_user_info(access_token)

            if user_info.properties and user_info.properties.nickname:
                return user_info.properties.nickname

            return None

        except Exception as e:
            print(f"Warning: Error extracting nickname from KakaoTalk: {str(e)}")
            return None

    async def get_user_profile_image(self, access_token: str) -> Optional[str]:
        """
        Extract profile image URL from KakaoTalk user information.

        Args:
            access_token: KakaoTalk access token

        Returns:
            Optional[str]: User profile image URL if available, None otherwise
        """
        try:
            user_info = await self.get_user_info(access_token)

            if user_info.properties and user_info.properties.profile_image:
                return user_info.properties.profile_image

            return None

        except Exception as e:
            print(f"Warning: Error extracting profile image from KakaoTalk: {str(e)}")
            return None

    async def authenticate_with_kakao(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete OAuth flow: exchange code for token and retrieve user info.

        This is a convenience method combining code-to-token exchange and
        user information retrieval.

        Args:
            code: Authorization code from KakaoTalk OAuth callback
            redirect_uri: Optional override of default redirect URI

        Returns:
            Dict with keys:
                - access_token: KakaoTalk access token
                - token_type: Token type (usually 'bearer')
                - expires_in: Token expiration in seconds
                - user_info: KakaoUserInfo with user details
                - kakao_id: KakaoTalk user ID
                - email: User email (if available)
                - nickname: User nickname (if available)
                - profile_image: User profile image URL (if available)

        Raises:
            ValueError: If code is invalid or exchange fails
            Exception: If network request fails
        """
        try:
            # Exchange code for token
            token_response = await self.exchange_code_for_token(code, redirect_uri)

            # Get user info
            user_info = await self.get_user_info(token_response.access_token)

            # Extract additional info
            email = await self.get_user_email(token_response.access_token)
            nickname = await self.get_user_nickname(token_response.access_token)
            profile_image = await self.get_user_profile_image(token_response.access_token)

            return {
                "access_token": token_response.access_token,
                "token_type": token_response.token_type,
                "expires_in": token_response.expires_in,
                "refresh_token": token_response.refresh_token,
                "user_info": user_info,
                "kakao_id": str(user_info.id),
                "email": email,
                "nickname": nickname,
                "profile_image": profile_image,
            }

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Error authenticating with KakaoTalk: {str(e)}")


# Global service instance
_kakao_oauth_service: Optional[KakaoOAuthService] = None


def get_kakao_oauth_service() -> KakaoOAuthService:
    """Get or create the KakaoTalk OAuth service instance."""
    global _kakao_oauth_service
    if _kakao_oauth_service is None:
        _kakao_oauth_service = KakaoOAuthService()
    return _kakao_oauth_service
