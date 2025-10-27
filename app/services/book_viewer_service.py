"""
Book Viewer Service

Provides utilities to fetch and serve PDF preview assets for books. The service
is designed to power the `/books/[id]/viewer` page in the Next.js frontend by
exposing both metadata and a streaming endpoint for the PDF file.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pypdf import PdfReader

from app.models.book_viewer import BookPdfManifestEntry, BookPdfMetadata, BookViewerPayload
from app.services.book_service import get_book_service


class BookViewerError(Exception):
    """Base class for viewer-related exceptions."""


class BookNotFoundError(BookViewerError):
    """Raised when a book cannot be located in the datastore."""


class PdfNotFoundError(BookViewerError):
    """Raised when a PDF asset cannot be located on disk."""


class BookViewerService:
    """Service class responsible for managing book PDF viewer assets."""

    DEFAULT_API_BASE_URL = "http://localhost:8000"

    def __init__(
        self,
        pdf_root: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        api_base_url: Optional[str] = None,
    ):
        self.pdf_root = pdf_root or Path(__file__).resolve().parent.parent / "static" / "pdfs"
        self.manifest_path = manifest_path or (self.pdf_root / "manifest.json")
        self.api_base_url = (api_base_url or os.getenv("API_BASE_URL") or self.DEFAULT_API_BASE_URL).rstrip("/")

        # Cache manifest entries to avoid re-reading from disk on every request
        self._manifest_index: Dict[str, BookPdfManifestEntry] = self._load_manifest()

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    def get_viewer_payload(self, book_id: str) -> BookViewerPayload:
        """
        Build the viewer payload for a book consisting of the book data,
        PDF metadata, and a streaming URL.
        """
        book_service = get_book_service()
        book = book_service.get_book_by_id(book_id)

        if book is None:
            raise BookNotFoundError(f"Book with ID '{book_id}' was not found.")

        pdf_metadata = self.get_pdf_metadata(book_id)

        stream_url = f"{self.api_base_url}/api/books/{book_id}/viewer/stream"

        return BookViewerPayload(
            book=book.model_dump(),
            pdf=pdf_metadata,
            stream_url=stream_url,
        )

    def get_pdf_metadata(self, book_id: str) -> BookPdfMetadata:
        """Return metadata for the PDF associated with a book."""
        pdf_path, is_fallback = self._resolve_pdf_path(book_id)

        if not pdf_path.exists():
            raise PdfNotFoundError(f"No PDF file found for book '{book_id}'.")

        stat = pdf_path.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime)

        try:
            reader = PdfReader(str(pdf_path))
            page_count = len(reader.pages)
        except Exception as exc:
            raise BookViewerError(f"Failed to read PDF metadata for '{book_id}': {exc}") from exc

        metadata = BookPdfMetadata(
            book_id=book_id,
            filename=pdf_path.name,
            page_count=page_count,
            file_size=stat.st_size,
            last_modified=last_modified,
            source=None,
        )

        return metadata

    def open_pdf(self, book_id: str):
        """Open the PDF file associated with a book and return a binary handle."""
        pdf_path, _ = self._resolve_pdf_path(book_id)
        if not pdf_path.exists():
            raise PdfNotFoundError(f"No PDF file found for book '{book_id}'.")
        return pdf_path.open("rb")

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _load_manifest(self) -> Dict[str, BookPdfManifestEntry]:
        """Load manifest entries from disk, if available."""
        if not self.manifest_path.exists():
            return {}

        try:
            raw_manifest = json.loads(self.manifest_path.read_text())
        except json.JSONDecodeError as exc:
            raise BookViewerError(f"Invalid PDF manifest file: {exc}") from exc

        manifest_entries: List[BookPdfManifestEntry] = [
            BookPdfManifestEntry(**entry) for entry in raw_manifest
        ]

        return {entry.book_id: entry for entry in manifest_entries}

    def _resolve_pdf_path(self, book_id: str) -> Tuple[Path, bool]:
        """
        Determine the filesystem path for a book's PDF.

        Returns a tuple of (path, is_fallback) where `is_fallback` indicates
        whether the default sample PDF is being used.
        """
        # 1. Check manifest override
        manifest_entry = self._manifest_index.get(book_id)
        if manifest_entry:
            candidate = self.pdf_root / manifest_entry.filename
            if candidate.exists():
                return candidate, False

        # 2. Check standard naming convention
        candidate = self.pdf_root / f"{book_id}.pdf"
        if candidate.exists():
            return candidate, False

        # 3. Fallback to sample PDF
        fallback = self.pdf_root / "sample.pdf"
        if fallback.exists():
            return fallback, True

        raise PdfNotFoundError(
            f"PDF for book '{book_id}' could not be located. "
            "Ensure a matching PDF exists or add an entry to the manifest."
        )


# Convenience factory
def get_book_viewer_service() -> BookViewerService:
    """Return a viewer service instance."""
    return BookViewerService()
