"""
Book Viewer Models

Defines the Pydantic models used by the PDF viewer endpoints. These models
describe metadata for PDF assets associated with books so the frontend can
render a document viewer for `/books/[id]/viewer`.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class BookPdfMetadata(BaseModel):
    """Metadata describing a PDF asset for a specific book."""

    book_id: str = Field(..., description="Identifier of the book this PDF belongs to")
    filename: str = Field(..., description="Name of the PDF file")
    page_count: int = Field(..., ge=1, description="Total number of pages in the PDF")
    file_size: int = Field(..., ge=0, description="Size of the PDF in bytes")
    mime_type: str = Field(default="application/pdf", description="MIME type of the asset")
    last_modified: datetime = Field(..., description="Timestamp when the PDF was last updated")
    source: Optional[HttpUrl] = Field(
        None,
        description="Optional canonical URL of the PDF (if served from CDN or storage bucket)",
    )


class BookViewerPayload(BaseModel):
    """
    Response payload for the book viewer endpoint combining the book metadata
    with the PDF asset details and the API URL to stream the PDF.
    """

    book: dict = Field(..., description="Serialized book data returned from Firestore")
    pdf: BookPdfMetadata = Field(..., description="Metadata about the PDF asset")
    stream_url: HttpUrl = Field(..., description="API URL used to stream/download the PDF")


class BookPdfManifestEntry(BaseModel):
    """
    Represents a manifest entry mapping a book ID to a local PDF file.
    This allows swapping out default behaviour without touching code.
    """

    book_id: str = Field(..., description="Book identifier")
    filename: str = Field(..., description="PDF filename relative to the PDF root directory")

