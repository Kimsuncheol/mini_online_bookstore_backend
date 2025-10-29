# PDF Operations Quick Reference Guide

A quick guide for developers using PDF functionality in the Mini Online Bookstore backend.

---

## Quick Start

### Get PDF Preview for Summaries

```python
from app.services.book_service import get_book_service

service = get_book_service()

# Get PDF preview (first 1000 chars)
preview = service.get_pdf_preview_text(
    book_id="book_123",
    max_chars=1000,
    chunk_size=900,
    chunk_overlap=150
)

if preview:
    print(preview[:200])  # Print first 200 chars
else:
    print("PDF not available for this book")
```

### Load PDF as Documents for AI Processing

```python
from app.services.book_service import get_book_service

service = get_book_service()

# Load PDF and split into chunks
documents = service.load_and_split_book_pdf(
    book_id="book_123",
    chunk_size=1000,
    chunk_overlap=200
)

for doc in documents:
    print(f"Page {doc.metadata.get('page')}: {doc.page_content[:100]}")
```

### Download Raw PDF Bytes

```python
from app.services.book_service import get_book_service

service = get_book_service()

# Download raw PDF bytes
pdf_bytes = service.download_book_pdf(book_id="book_123")

if pdf_bytes:
    with open("downloaded_book.pdf", "wb") as f:
        f.write(pdf_bytes)
else:
    print("PDF download failed")
```

---

## Common Use Cases

### 1. AI Summary Generation with PDF Context

```python
from app.services.book_service import get_book_service
from app.services.book_summary_service import get_book_summary_service
from app.models.book import Book

async def generate_summary_with_context(book: Book):
    book_service = get_book_service()
    summary_service = get_book_summary_service()

    # Get PDF preview for context
    pdf_preview = book_service.get_pdf_preview_text(
        book,
        max_chars=1000,
        chunk_size=900,
        chunk_overlap=150
    )

    # Generate summary (uses preview internally)
    summary = await summary_service.generate_summary_for_book(book)

    return summary
```

### 2. AI Search with PDF Snippets

```python
from app.services.ai_search_service import get_ai_search_service

async def search_books_with_previews(question: str, user_email: str):
    search_service = get_ai_search_service()

    # Search will automatically include PDF previews for top results
    result = await search_service.search_with_ai(
        question=question,
        user_email=user_email
    )

    return result  # Contains recommended_books with preview text
```

### 3. Batch PDF Processing

```python
from app.services.book_service import get_book_service
from typing import List

async def process_all_pdfs_for_indexing(limit: int = 100):
    service = get_book_service()
    books = service.get_all_books(limit=limit)

    for book in books:
        try:
            # Load and split PDF for indexing
            chunks = service.load_and_split_book_pdf(
                book,
                chunk_size=800,
                chunk_overlap=200
            )

            # Process chunks (e.g., create embeddings)
            for chunk in chunks:
                print(f"Processing chunk from {book.title}")
                # Your processing logic here

        except Exception as e:
            print(f"Warning: Failed to process {book.id}: {str(e)}")
            continue  # Continue with next book
```

### 4. Extract PDF Text for Search Index

```python
from app.services.book_service import get_book_service

def extract_full_pdf_text(book_id: str) -> str:
    service = get_book_service()

    # Load PDF documents
    documents = service.load_book_pdf_documents(book_id)

    if not documents:
        return ""

    # Combine all page content
    full_text = "\n\n".join(doc.page_content for doc in documents)
    return full_text
```

---

## API Reference

### Book Service PDF Methods

#### `download_book_pdf(book_or_id, raise_errors=False)`

Downloads raw PDF bytes from Firebase Storage.

**Parameters**:
- `book_or_id` (Union[Book, str]): Book instance or book ID
- `raise_errors` (bool): If True, raises exceptions; if False, returns None

**Returns**: `Optional[bytes]` - PDF content or None

**Example**:
```python
pdf_bytes = service.download_book_pdf("book_123", raise_errors=True)
```

---

#### `load_book_pdf_documents(book_or_id, raise_errors=False)`

Loads PDF pages as LangChain Document objects without splitting.

**Parameters**:
- `book_or_id` (Union[Book, str]): Book instance or book ID
- `raise_errors` (bool): If True, raises exceptions; if False, returns empty list

**Returns**: `List[Document]` - One Document per PDF page

**Example**:
```python
documents = service.load_book_pdf_documents("book_123")
print(f"Loaded {len(documents)} pages")
```

---

#### `load_and_split_book_pdf(book_or_id, chunk_size=1000, chunk_overlap=200, raise_errors=False)`

Loads PDF and splits text using recursive character splitting.

**Parameters**:
- `book_or_id` (Union[Book, str]): Book instance or book ID
- `chunk_size` (int): Target chunk size in characters (default: 1000)
- `chunk_overlap` (int): Overlapping chars between chunks (default: 200)
- `raise_errors` (bool): If True, raises exceptions; if False, returns empty list

**Returns**: `List[Document]` - Split document chunks with metadata

**Example**:
```python
chunks = service.load_and_split_book_pdf(
    "book_123",
    chunk_size=800,
    chunk_overlap=150
)
print(f"Split into {len(chunks)} chunks")
```

---

#### `get_pdf_preview_text(book_or_id, max_chars=2000, chunk_size=900, chunk_overlap=150)`

Extracts preview text from PDF for AI context.

**Parameters**:
- `book_or_id` (Union[Book, str]): Book instance or book ID
- `max_chars` (int): Maximum characters to extract (default: 2000)
- `chunk_size` (int): Chunk size for splitting (default: 900)
- `chunk_overlap` (int): Chunk overlap (default: 150)

**Returns**: `Optional[str]` - Preview text or None

**Example**:
```python
preview = service.get_pdf_preview_text("book_123", max_chars=500)
if preview:
    print(f"Preview ({len(preview)} chars):\n{preview}")
```

---

## Error Handling

### Exception Types

```python
from app.utils.pdf_loader import (
    PDFLoaderError,
    PDFNotFoundError,
    PDFProcessingError
)
```

### Handling Errors

```python
from app.services.book_service import get_book_service
from app.utils.pdf_loader import PDFNotFoundError, PDFProcessingError

service = get_book_service()

try:
    preview = service.get_pdf_preview_text("book_123")
    if preview:
        print(f"Got preview: {preview[:100]}")
    else:
        print("No preview available (PDF might not exist)")
except PDFNotFoundError:
    print("PDF file not found in Firebase Storage")
except PDFProcessingError as e:
    print(f"Failed to process PDF: {str(e)}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

### Best Practice: Graceful Degradation

```python
def generate_summary_safely(book_id: str):
    service = get_book_service()

    # Get PDF preview (optional, service continues without it)
    pdf_preview = service.get_pdf_preview_text(book_id)

    if pdf_preview:
        print(f"Using PDF context: {pdf_preview[:100]}")
        # Generate summary with PDF context
    else:
        print("Generating summary without PDF context")
        # Generate summary with book metadata only
```

---

## Performance Tips

### 1. Preview-Only for Speed

For real-time operations (summaries, search), use preview extraction:

```python
# ✅ FAST: 200-400ms
preview = service.get_pdf_preview_text(book, max_chars=1000)

# ❌ SLOW: 2-5 seconds
documents = service.load_and_split_book_pdf(book)
```

### 2. Limit Books Processed

For batch operations, limit the number of books:

```python
# ✅ GOOD: Process top 3 books
top_books = books[:3]
for book in top_books:
    preview = service.get_pdf_preview_text(book)

# ❌ BAD: Process all 1000 books
for book in all_books:  # Very slow!
    preview = service.get_pdf_preview_text(book)
```

### 3. Adjust Chunk Parameters

Balance quality vs. speed:

```python
# ✅ FAST: Larger chunks
chunks = service.load_and_split_book_pdf(
    book,
    chunk_size=2000,    # Larger chunks = fewer splits
    chunk_overlap=400
)

# ✅ QUALITY: Smaller chunks for better precision
chunks = service.load_and_split_book_pdf(
    book,
    chunk_size=500,     # Smaller chunks = more context windows
    chunk_overlap=100
)
```

---

## Configuration Reference

### Default Values

```python
class BookService:
    DEFAULT_PDF_CHUNK_SIZE = 1000       # Characters per chunk
    DEFAULT_PDF_CHUNK_OVERLAP = 200     # Overlap between chunks
    DEFAULT_PDF_PREVIEW_CHARS = 2000    # Default preview length
```

### Recommended Values by Use Case

| Use Case | chunk_size | chunk_overlap | max_chars |
|----------|-----------|---------------|-----------|
| Summary Context | 900 | 150 | 1000 |
| Search Preview | 700 | 120 | 600 |
| Full Processing | 1000 | 200 | N/A |
| Fast Context | 1500 | 300 | 300 |

---

## Advanced Examples

### Creating Vector Embeddings

```python
from app.services.book_service import get_book_service
from langchain_openai import OpenAIEmbeddings

async def create_pdf_embeddings(book_id: str):
    service = get_book_service()
    embeddings = OpenAIEmbeddings()

    # Load PDF chunks
    chunks = service.load_and_split_book_pdf(
        book_id,
        chunk_size=800,
        chunk_overlap=200
    )

    # Create embeddings for each chunk
    chunk_embeddings = []
    for chunk in chunks:
        embedding = embeddings.embed_query(chunk.page_content)
        chunk_embeddings.append({
            "text": chunk.page_content,
            "embedding": embedding,
            "metadata": chunk.metadata
        })

    return chunk_embeddings
```

### Combining PDF with Metadata for RAG

```python
def prepare_rag_context(book_id: str):
    service = get_book_service()

    # Get book metadata
    book = service.get_book_by_id(book_id)

    # Get PDF preview
    preview = service.get_pdf_preview_text(book, max_chars=1500)

    # Combine for RAG context
    rag_context = f"""
    Book: {book.title}
    Author: {book.author}
    Genre: {book.genre}
    Description: {book.description}

    Content Preview:
    {preview}
    """

    return rag_context
```

---

## Troubleshooting

### PDF Not Found

```python
# Check if book has pdf_file_name set
book = service.get_book_by_id("book_123")
if not book.pdf_file_name:
    print("❌ PDF path not set for this book")
    print(f"   Set book.pdf_file_name to Firebase Storage path")
else:
    print(f"✅ PDF path: {book.pdf_file_name}")
```

### PDF Processing Slow

```python
# Try with larger chunks to reduce processing time
chunks = service.load_and_split_book_pdf(
    book,
    chunk_size=2000,     # Increase from 1000
    chunk_overlap=400    # Increase from 200
)
```

### Memory Issues

```python
# Process in smaller batches
books = service.get_all_books(limit=1000)

for i in range(0, len(books), 10):
    batch = books[i:i+10]
    for book in batch:
        # Process book
        pass

    # Clear memory between batches
    import gc
    gc.collect()
```

---

## Testing

### Unit Test Example

```python
import pytest
from app.services.book_service import get_book_service

@pytest.fixture
def book_service():
    return get_book_service()

def test_get_pdf_preview_text(book_service):
    # Test with a real book that has PDF
    preview = book_service.get_pdf_preview_text("book_123")

    assert preview is not None
    assert len(preview) > 0
    assert len(preview) <= 2000

def test_pdf_not_found(book_service):
    # Test with non-existent book
    preview = book_service.get_pdf_preview_text("nonexistent_book")

    assert preview is None
```

---

## Resources

- **Main Documentation**: [PDF_LOADER_ARCHITECTURE.md](./PDF_LOADER_ARCHITECTURE.md)
- **Model Verification**: [BOOK_MODEL_VERIFICATION.md](./BOOK_MODEL_VERIFICATION.md)
- **Implementation Status**: [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)
- **Source Code**: `app/utils/pdf_loader.py`, `app/services/book_service.py`

---

## Support

For issues or questions:
1. Check the architecture documentation
2. Review error handling patterns
3. Check logs for specific error messages
4. Verify Firebase credentials are configured

---

**Last Updated**: 2025-10-29
**Version**: 1.0
