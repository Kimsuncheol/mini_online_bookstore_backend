"""
Firebase Configuration Module

This module handles the initialization and configuration of Firebase Admin SDK.
It provides a centralized way to initialize Firebase app and access Firestore database.
"""

import os
import json
from pathlib import Path
from typing import Optional, Any
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from app.utils.mock_firestore import MockFirestore

# Load environment variables from .env file
load_dotenv()


class FirebaseConfig:
    """
    Firebase configuration class that initializes Firebase Admin SDK
    and provides access to Firestore database.
    """

    _app: Optional[firebase_admin.App] = None
    _db: Optional[Any] = None
    _initialized: bool = False
    _using_mock: bool = False

    @staticmethod
    def _is_truthy(value: Optional[str]) -> bool:
        """Convert common truthy strings to boolean."""
        if value is None:
            return False
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}

    @classmethod
    def initialize(cls) -> None:
        """
        Initialize Firebase Admin SDK.

        Supports two methods of initialization:
        1. Using a service account JSON file (FIREBASE_CREDENTIALS_PATH)
        2. Using environment variables for service account details

        Raises:
            ValueError: If neither credentials path nor required environment variables are provided
            FileNotFoundError: If the credentials file path is invalid
        """
        if cls._initialized:
            print("Firebase app is already initialized")
            return

        cls._db = None
        cls._app = None
        cls._using_mock = False

        use_mock = cls._is_truthy(os.getenv("FIREBASE_USE_MOCK"))
        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH") or os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")
        app_options = {"storageBucket": storage_bucket} if storage_bucket else None

        try:
            if not use_mock and credentials_path:
                # Method 1: Initialize using service account JSON file
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(
                        f"Firebase credentials file not found at: {credentials_path}"
                    )

                cred = credentials.Certificate(credentials_path)
                cls._app = firebase_admin.initialize_app(cred, app_options)
                cls._db = firestore.client()
                print(f"✓ Firebase initialized using credentials file: {credentials_path}")
            elif not use_mock:
                # Method 2: Initialize using environment variables
                service_account_config = cls._build_service_account_from_env()
                if not service_account_config:
                    raise ValueError(
                        "Firebase initialization failed. Please provide either:\n"
                        "1. FIREBASE_CREDENTIALS_PATH environment variable pointing to a service account JSON file, or\n"
                        "2. All required Firebase service account environment variables:\n"
                        "   - FIREBASE_TYPE\n"
                        "   - FIREBASE_PROJECT_ID\n"
                        "   - FIREBASE_PRIVATE_KEY_ID\n"
                        "   - FIREBASE_PRIVATE_KEY\n"
                        "   - FIREBASE_CLIENT_EMAIL\n"
                        "   - FIREBASE_CLIENT_ID\n"
                        "   - FIREBASE_AUTH_URI\n"
                        "   - FIREBASE_TOKEN_URI\n"
                        "   - FIREBASE_AUTH_PROVIDER_X509_CERT_URL\n"
                        "   - FIREBASE_CLIENT_X509_CERT_URL"
                    )

                cred = credentials.Certificate(service_account_config)
                cls._app = firebase_admin.initialize_app(cred, app_options)
                cls._db = firestore.client()
                print("✓ Firebase initialized using environment variables")
            else:
                cls._using_mock = True
                cls._db = MockFirestore()
                print("WARNING: Firebase credentials not provided. Using in-memory Firestore mock.")
        except (FileNotFoundError, ValueError) as init_error:
            # Fall back to mock Firestore if configured to do so implicitly
            if use_mock or cls._is_truthy(os.getenv("FIREBASE_ALLOW_MOCK_FALLBACK", "true")):
                cls._using_mock = True
                cls._db = MockFirestore()
                print(
                    f"WARNING: {str(init_error)}\n"
                    "WARNING: Falling back to in-memory Firestore mock. Set FIREBASE_USE_MOCK=false "
                    "and provide valid credentials to use Firebase."
                )
            else:
                raise

        cls._initialized = True

    @classmethod
    def _build_service_account_from_env(cls) -> Optional[dict]:
        """
        Build service account configuration dictionary from environment variables.

        Returns:
            dict: Service account configuration if all required env vars are present, None otherwise
        """
        required_keys = [
            "FIREBASE_TYPE",
            "FIREBASE_PROJECT_ID",
            "FIREBASE_PRIVATE_KEY_ID",
            "FIREBASE_PRIVATE_KEY",
            "FIREBASE_CLIENT_EMAIL",
            "FIREBASE_CLIENT_ID",
            "FIREBASE_AUTH_URI",
            "FIREBASE_TOKEN_URI",
            "FIREBASE_AUTH_PROVIDER_X509_CERT_URL",
            "FIREBASE_CLIENT_X509_CERT_URL",
        ]

        # Check if all required environment variables are present
        if not all(os.getenv(key) for key in required_keys):
            return None

        # Build service account configuration
        return {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
        }

    @classmethod
    def get_db(cls) -> Any:
        """
        Get Firestore database client instance.

        Initializes Firebase if not already initialized.

        Returns:
            Any: Firestore database client instance
        """
        if not cls._initialized:
            cls.initialize()

        if cls._db is None and not cls._using_mock:
            cls._db = firestore.client()

        return cls._db

    @classmethod
    def get_app(cls) -> firebase_admin.App:
        """
        Get Firebase app instance.

        Initializes Firebase if not already initialized.

        Returns:
            firebase_admin.App: Firebase app instance
        """
        if not cls._initialized:
            cls.initialize()

        if cls._using_mock:
            raise RuntimeError("Firebase mock mode active; no Firebase app instance available.")

        if cls._app is None:
            raise RuntimeError("Firebase app is not initialized.")

        return cls._app

    @classmethod
    def close(cls) -> None:
        """
        Close Firebase connection and cleanup resources.
        """
        if not cls._initialized:
            return

        if cls._using_mock:
            cls._db = None
            cls._app = None
            print("✓ Firebase mock connection closed")
        elif cls._app is not None:
            firebase_admin.delete_app(cls._app)
            cls._app = None
            cls._db = None
            print("✓ Firebase connection closed")

        cls._initialized = False
        cls._using_mock = False


# Convenience function to initialize Firebase
def init_firebase() -> None:
    """Initialize Firebase Admin SDK."""
    FirebaseConfig.initialize()


# Convenience function to get Firestore client
def get_firestore_client() -> Any:
    """Get Firestore database client."""
    return FirebaseConfig.get_db()
