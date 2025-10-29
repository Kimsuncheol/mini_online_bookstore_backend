# PDF Loader Quick Start

## Installation Complete ✓

The PDF loader utility has been successfully implemented with full semantic chunking support.

## One-Liner Examples

### Load and Split PDF from Firebase Storage
```python
from app.utils.pdf_loader import load_and_split_pdf_from_storage

chunks = load_and_split_pdf_from_storage('pdfs/book.pdf')
```

### Load and Split from Local File
```python
from app.utils.pdf_loader import load_and_split_pdf_from_local

chunks = load_and_split_pdf_from_local('/path/to/book.pdf')
```

### Just Load (No Splitting)
```python
from app.utils.pdf_loader import load_pdf_from_storage

documents = load_pdf_from_storage('pdfs/book.pdf')
```

## Common Parameters

```python
load_and_split_pdf_from_storage(
    bucket_path='pdfs/book.pdf',                    # Required: Firebase path
    chunk_size=1000,                                # Optional: Target chunk size
    break_point_percentile_threshold=95,            # Optional: Semantic threshold
    use_semantic_chunking=True                      # Optional: Enable/disable semantic chunking
)
```

### Parameter Quick Reference

| Parameter | Default | Notes |
|-----------|---------|-------|
| `bucket_path` | Required | Path in Firebase Storage (e.g., 'pdfs/book123.pdf') |
| `chunk_size` | 1000 | Target characters per chunk |
| `break_point_percentile_threshold` | 95 | Higher = larger chunks, Lower = smaller chunks |
| `use_semantic_chunking` | True | Set to False for basic splitting (faster, no API cost) |

## Threshold Guidelines

- **98+**: Conservative (large chunks, fewer API calls)
- **95**: Balanced (default, recommended for most cases)
- **90**: Moderate (medium chunks, good balance)
- **75**: Aggressive (small chunks, more API calls)

## Usage in a Service

```python
from app.utils.pdf_loader import load_and_split_pdf_from_storage, PDFLoaderError

class MyService:
    def process_book_pdf(self, book_id: str):
        try:
            chunks = load_and_split_pdf_from_storage(
                f'books/{book_id}.pdf',
                chunk_size=800
            )
            # Do something with chunks
            return chunks
        except PDFLoaderError as e:
            # Handle error
            raise
```

## API Endpoints Integration Example

```python
from fastapi import APIRouter, HTTPException
from app.utils.pdf_loader import load_and_split_pdf_from_storage

router = APIRouter(prefix="/api/pdf", tags=["pdf"])

@router.post("/load-book/{book_id}")
async def load_book_pdf(book_id: str):
    try:
        chunks = load_and_split_pdf_from_storage(f'books/{book_id}.pdf')
        return {
            "success": True,
            "chunk_count": len(chunks),
            "chunks": [
                {"page": c.metadata.get('page'), "content": c.page_content}
                for c in chunks
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Available Functions

### Loading Functions
- `load_pdf_from_storage(bucket_path)` - Load from Firebase
- `load_pdf_from_local_path(file_path)` - Load from filesystem
- `download_pdf_from_storage(bucket_path)` - Download raw bytes

### Combined Functions (Load + Split)
- `load_and_split_pdf_from_storage(bucket_path, ...)` - Firebase (recommended)
- `load_and_split_pdf_from_local(file_path, ...)` - Local file

### Splitting Functions
- `split_pdf_text(documents, ...)` - Split already-loaded documents

### Other
- `get_firebase_storage()` - Direct bucket access

## Exception Handling

```python
from app.utils.pdf_loader import (
    load_and_split_pdf_from_storage,
    PDFNotFoundError,
    PDFProcessingError
)

try:
    chunks = load_and_split_pdf_from_storage('pdfs/book.pdf')
except PDFNotFoundError:
    # File doesn't exist in storage
    pass
except PDFProcessingError:
    # PDF is corrupt or processing failed
    pass
```

## Performance Notes

- **Semantic Chunking**: Calls OpenAI embeddings API (costs money!)
- **Basic Splitting**: Fast, free, but less intelligent
- **Firebase Latency**: ~100-500ms download time
- **Processing**: ~100ms per page + API calls for semantic chunking

## Environment Setup

Required environment variables:
- `OPENAI_API_KEY` - For semantic chunking (embeddings)
- Firebase credentials (already configured)

## Document Output

Each chunk/document includes:
- `page_content`: The actual text
- `metadata`: Dictionary with:
  - `source`: File path
  - `storage_type`: 'firebase_storage' or 'local'
  - `page`: Page number
  - Additional PDF metadata

## File Location

Implementation: `app/utils/pdf_loader.py`
Tests can be added to: `tests/utils/test_pdf_loader.py`

## Next Steps

1. Try loading a sample PDF: `chunks = load_and_split_pdf_from_storage('pdfs/sample.pdf')`
2. Integrate into a service or router
3. Experiment with different `break_point_percentile_threshold` values
4. Monitor OpenAI API usage for cost tracking

For detailed documentation, see [PDF_LOADER_GUIDE.md](PDF_LOADER_GUIDE.md)
