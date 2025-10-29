"""
PDF Loader Utility

Provides utility functions to load PDF files from Firebase Storage
and split their text using LangChain's semantic chunking.

Uses:
- PyMuPDFLoader: For loading PDF documents
- SemanticChunker: For intelligent text splitting based on semantic similarity
- OpenAIEmbeddings: For computing embeddings to determine semantic boundaries
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document

from app.utils.firebase_config import FirebaseConfig


class PDFLoaderError(Exception):
    """Base exception for PDF loading operations."""
    pass


class PDFNotFoundError(PDFLoaderError):
    """Raised when a PDF file is not found in Firebase Storage."""
    pass


class PDFProcessingError(PDFLoaderError):
    """Raised when PDF processing fails."""
    pass


def get_firebase_storage():
    """
    Get Firebase Storage bucket instance.

    Returns:
        google.cloud.storage.bucket.Bucket: Firebase Storage bucket

    Raises:
        RuntimeError: If Firebase app is not initialized
    """
    try:
        FirebaseConfig.get_app()
        from firebase_admin import storage
        return storage.bucket()
    except RuntimeError:
        raise PDFLoaderError(
            "Firebase app not initialized. Ensure Firebase credentials are configured."
        )
    except Exception as e:
        raise PDFLoaderError(f"Failed to access Firebase Storage: {str(e)}")


def download_pdf_from_storage(
    bucket_path: str,
    bucket_name: Optional[str] = None,  # Reserved for future custom bucket support
) -> bytes:
    """
    Download a PDF file from Firebase Storage.

    Args:
        bucket_path (str): Path to the PDF file in Firebase Storage (e.g., 'pdfs/book123.pdf')
        bucket_name (Optional[str]): Firebase Storage bucket name. Currently unused;
                                     reserved for future custom bucket support.

    Returns:
        bytes: PDF file content as bytes

    Raises:
        PDFNotFoundError: If the file doesn't exist in Storage
        PDFLoaderError: If download fails
    """
    try:
        bucket = get_firebase_storage()

        # Get the blob (file object)
        blob = bucket.blob(bucket_path)

        if not blob.exists():
            raise PDFNotFoundError(
                f"PDF file not found in Firebase Storage: {bucket_path}"
            )

        # Download the file content to bytes
        pdf_content = blob.download_as_bytes()
        return pdf_content

    except PDFNotFoundError:
        raise
    except Exception as e:
        raise PDFLoaderError(
            f"Failed to download PDF from Firebase Storage ({bucket_path}): {str(e)}"
        )


def load_pdf_from_storage(
    bucket_path: str,
    bucket_name: Optional[str] = None,
) -> List[Document]:
    """
    Load a PDF file from Firebase Storage and extract its content as documents.

    Args:
        bucket_path (str): Path to the PDF file in Firebase Storage
        bucket_name (Optional[str]): Firebase Storage bucket name (unused currently, for future use)

    Returns:
        List[Document]: List of LangChain Document objects with page content and metadata

    Raises:
        PDFNotFoundError: If the file doesn't exist
        PDFProcessingError: If PDF loading fails
    """
    try:
        # Download PDF from Firebase Storage
        pdf_content = download_pdf_from_storage(bucket_path, bucket_name)

        # Create a temporary file to store the PDF
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as temp_file:
            temp_file.write(pdf_content)
            temp_path = temp_file.name

        try:
            # Use PyMuPDFLoader to load the PDF
            loader = PyMuPDFLoader(temp_path)
            documents = loader.load()

            # Add metadata about the source
            for doc in documents:
                doc.metadata["source"] = bucket_path
                doc.metadata["storage_type"] = "firebase_storage"

            return documents

        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    except PDFNotFoundError:
        raise
    except Exception as e:
        raise PDFProcessingError(f"Failed to load PDF from storage: {str(e)}")


def split_pdf_text(
    documents: List[Document],
    chunk_size: int = 1000,
    break_point_percentile_threshold: int = 95,
    use_semantic_chunking: bool = True,
) -> List[Document]:
    """
    Split PDF text using semantic chunking based on semantic similarity.

    The SemanticChunker uses embeddings to find the most coherent chunk
    boundaries by looking at the semantic similarity between consecutive chunks.

    Args:
        documents (List[Document]): List of documents from PDF loader
        chunk_size (int): Target chunk size in characters (default: 1000)
        break_point_percentile_threshold (int): Percentile threshold for determining
                                               breakpoints based on semantic distance
                                               (default: 95, meaning breaks at larger distances)
        use_semantic_chunking (bool): Whether to use semantic chunking. If False,
                                     uses basic character splitting (default: True)

    Returns:
        List[Document]: List of split documents with semantic awareness

    Raises:
        PDFProcessingError: If splitting fails
    """
    try:
        if not documents:
            return []

        if not use_semantic_chunking:
            # Fallback to simple character splitting
            from langchain_text_splitters import CharacterTextSplitter

            splitter = CharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=200,
                separator="\n",
            )
            return splitter.split_documents(documents)

        # Use SemanticChunker for intelligent splitting
        embeddings = OpenAIEmbeddings()

        semantic_splitter = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=break_point_percentile_threshold,
        )

        split_docs = semantic_splitter.split_documents(documents)
        return split_docs

    except Exception as e:
        raise PDFProcessingError(f"Failed to split PDF text: {str(e)}")


def load_and_split_pdf_from_storage(
    bucket_path: str,
    bucket_name: Optional[str] = None,
    chunk_size: int = 1000,
    break_point_percentile_threshold: int = 95,
    use_semantic_chunking: bool = True,
) -> List[Document]:
    """
    Load a PDF from Firebase Storage and split its text in one operation.

    This is a convenience function that combines load_pdf_from_storage
    and split_pdf_text operations.

    Args:
        bucket_path (str): Path to the PDF file in Firebase Storage
        bucket_name (Optional[str]): Firebase Storage bucket name
        chunk_size (int): Target chunk size in characters (default: 1000)
        break_point_percentile_threshold (int): Percentile threshold for semantic breaks
                                               (default: 95)
        use_semantic_chunking (bool): Whether to use semantic chunking (default: True)

    Returns:
        List[Document]: List of split documents with metadata

    Raises:
        PDFNotFoundError: If the PDF file doesn't exist
        PDFProcessingError: If loading or splitting fails
    """
    try:
        # Load PDF from Firebase Storage
        documents = load_pdf_from_storage(bucket_path, bucket_name)

        # Split the text
        split_documents = split_pdf_text(
            documents,
            chunk_size=chunk_size,
            break_point_percentile_threshold=break_point_percentile_threshold,
            use_semantic_chunking=use_semantic_chunking,
        )

        return split_documents

    except (PDFNotFoundError, PDFProcessingError):
        raise
    except Exception as e:
        raise PDFProcessingError(
            f"Failed to load and split PDF: {str(e)}"
        )


def load_pdf_from_local_path(
    file_path: str,
) -> List[Document]:
    """
    Load a PDF from a local file path.

    Useful for development and testing without Firebase Storage dependency.

    Args:
        file_path (str): Path to the PDF file on the local filesystem

    Returns:
        List[Document]: List of LangChain Document objects

    Raises:
        PDFNotFoundError: If the file doesn't exist
        PDFProcessingError: If PDF loading fails
    """
    try:
        path = Path(file_path)

        if not path.exists():
            raise PDFNotFoundError(f"PDF file not found: {file_path}")

        if not path.suffix.lower() == ".pdf":
            raise PDFProcessingError(f"File is not a PDF: {file_path}")

        # Use PyMuPDFLoader to load the PDF
        loader = PyMuPDFLoader(str(path))
        documents = loader.load()

        # Add metadata about the source
        for doc in documents:
            doc.metadata["source"] = file_path
            doc.metadata["storage_type"] = "local"

        return documents

    except (PDFNotFoundError, PDFProcessingError):
        raise
    except Exception as e:
        raise PDFProcessingError(f"Failed to load PDF from local path: {str(e)}")


def load_and_split_pdf_from_local(
    file_path: str,
    chunk_size: int = 1000,
    break_point_percentile_threshold: int = 95,
    use_semantic_chunking: bool = True,
) -> List[Document]:
    """
    Load a PDF from local filesystem and split its text in one operation.

    Useful for development and testing.

    Args:
        file_path (str): Path to the PDF file on the local filesystem
        chunk_size (int): Target chunk size in characters (default: 1000)
        break_point_percentile_threshold (int): Percentile threshold for semantic breaks
                                               (default: 95)
        use_semantic_chunking (bool): Whether to use semantic chunking (default: True)

    Returns:
        List[Document]: List of split documents with metadata

    Raises:
        PDFNotFoundError: If the PDF file doesn't exist
        PDFProcessingError: If loading or splitting fails
    """
    try:
        # Load PDF from local path
        documents = load_pdf_from_local_path(file_path)

        # Split the text
        split_documents = split_pdf_text(
            documents,
            chunk_size=chunk_size,
            break_point_percentile_threshold=break_point_percentile_threshold,
            use_semantic_chunking=use_semantic_chunking,
        )

        return split_documents

    except (PDFNotFoundError, PDFProcessingError):
        raise
    except Exception as e:
        raise PDFProcessingError(
            f"Failed to load and split PDF from local path: {str(e)}"
        )


__all__ = [
    "PDFLoaderError",
    "PDFNotFoundError",
    "PDFProcessingError",
    "get_firebase_storage",
    "download_pdf_from_storage",
    "load_pdf_from_storage",
    "split_pdf_text",
    "load_and_split_pdf_from_storage",
    "load_pdf_from_local_path",
    "load_and_split_pdf_from_local",
]