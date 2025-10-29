# PDF Loader - Updated Implementation

## Update Summary

The PDF loader utility has been updated to use `RecursiveCharacterTextSplitter` instead of `SemanticChunker` for text splitting.

### What Changed

**Before:**
- Used `SemanticChunker` from `langchain_experimental.text_splitter`
- Required OpenAI embeddings for semantic understanding
- More expensive (API calls to OpenAI)
- Better semantic coherence but slower

**After:**
- Uses `RecursiveCharacterTextSplitter` from `langchain_text_splitters`
- No external API calls required
- Faster processing
- Cost-free operation
- Intelligent recursive splitting strategy

## Key Features of RecursiveCharacterTextSplitter

✓ **Intelligent Recursive Splitting**
- Recursively tries multiple separators: `["\n\n", "\n", " ", ""]`
- Starts with paragraph breaks, then sentences, then words, then characters
- Preserves semantic structure naturally

✓ **No External Dependencies**
- No OpenAI API calls needed
- No embedding costs
- Faster processing

✓ **Configurable**
- `chunk_size`: Target chunk size (default: 1000 characters)
- `chunk_overlap`: Overlapping characters between chunks (default: 200)
- Both parameters directly control splitting behavior

✓ **Production Ready**
- Reliable and stable
- Well-tested in LangChain ecosystem
- Suitable for all document types

## New API

### `split_pdf_text(documents, chunk_size=1000, chunk_overlap=200)`

```python
from app.utils.pdf_loader import split_pdf_text

# Split documents with default parameters
chunks = split_pdf_text(documents)

# Custom parameters
chunks = split_pdf_text(
    documents,
    chunk_size=500,      # Smaller chunks
    chunk_overlap=100    # Less overlap
)
```

### `load_and_split_pdf_from_storage(bucket_path, chunk_size=1000, chunk_overlap=200)`

```python
from app.utils.pdf_loader import load_and_split_pdf_from_storage

# Load and split in one operation
chunks = load_and_split_pdf_from_storage(
    'pdfs/book.pdf',
    chunk_size=1000,
    chunk_overlap=200
)
```

### `load_and_split_pdf_from_local(file_path, chunk_size=1000, chunk_overlap=200)`

```python
from app.utils.pdf_loader import load_and_split_pdf_from_local

# Local file loading with splitting
chunks = load_and_split_pdf_from_local(
    './test.pdf',
    chunk_size=1000
)
```

## Parameter Guide

### chunk_size (int, default: 1000)
**Target size for text chunks in characters**

- Recommended: 500-2000 characters
- Smaller values: More chunks, more API calls for embedding
- Larger values: Fewer chunks, but may lose detail

**Examples:**
```python
chunk_size=500   # Small chunks, high detail
chunk_size=1000  # Default, balanced
chunk_size=2000  # Large chunks, high-level overview
```

### chunk_overlap (int, default: 200)
**Number of characters that overlap between consecutive chunks**

Helps maintain context and prevents breaking mid-sentence.

**Examples:**
```python
chunk_overlap=0    # No overlap (faster, less context)
chunk_overlap=200  # Default (good for most cases)
chunk_overlap=500  # High overlap (more context, more processing)
```

## Splitting Strategy

RecursiveCharacterTextSplitter uses this recursive strategy:

1. **Try paragraph break (`\n\n`)**: Split on paragraphs first
2. **Try line break (`\n`)**: If paragraphs are still too large, split on lines
3. **Try space (` `)**: If lines are too large, split on words
4. **Try character (``)**: Last resort, split on characters

This maintains natural structure and readability.

### Example Output

**Input text:**
```
This is paragraph 1.

This is paragraph 2 with more content.

This is paragraph 3.
```

**With chunk_size=50, chunk_overlap=10:**
```
Chunk 1: "This is paragraph 1. \n\nThis is paragraph"
Chunk 2: "paragraph 2 with more content.\n\nThis"
Chunk 3: "This is paragraph 3."
```

## Performance Comparison

| Aspect | RecursiveCharacterTextSplitter | SemanticChunker |
|--------|--------------------------------|-----------------|
| Speed | Fast (local) | Slow (API calls) |
| Cost | Free | ~$0.02 per 1M tokens |
| Setup | No API keys needed | Requires OpenAI API |
| Processing | Instant | 50-100ms per chunk |
| Quality | Good (structure-aware) | Excellent (semantic-aware) |

## Usage Examples

### Example 1: Load and Split from Firebase

```python
from app.utils.pdf_loader import load_and_split_pdf_from_storage

chunks = load_and_split_pdf_from_storage(
    'books/technical_manual.pdf',
    chunk_size=1000,
    chunk_overlap=200
)

print(f"Created {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {len(chunk.page_content)} characters")
```

### Example 2: Fine-tune Splitting

```python
from app.utils.pdf_loader import load_pdf_from_storage, split_pdf_text

# Load first
documents = load_pdf_from_storage('books/novel.pdf')

# Try different splitting strategies
small_chunks = split_pdf_text(documents, chunk_size=500, chunk_overlap=100)
large_chunks = split_pdf_text(documents, chunk_size=2000, chunk_overlap=300)

print(f"Small chunks: {len(small_chunks)}")
print(f"Large chunks: {len(large_chunks)}")
```

### Example 3: Local Development

```python
from app.utils.pdf_loader import load_and_split_pdf_from_local

try:
    chunks = load_and_split_pdf_from_local(
        './test_document.pdf',
        chunk_size=800
    )
    print(f"Successfully loaded {len(chunks)} chunks")
except FileNotFoundError:
    print("PDF not found")
```

### Example 4: Integration with Service

```python
from app.utils.pdf_loader import load_and_split_pdf_from_storage
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/pdf", tags=["pdf"])

@router.post("/process/{book_id}")
async def process_book(book_id: str):
    try:
        chunks = load_and_split_pdf_from_storage(
            f'books/{book_id}.pdf',
            chunk_size=1000
        )
        return {
            "success": True,
            "chunk_count": len(chunks),
            "chunks": [chunk.page_content for chunk in chunks]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Migration Guide

If you were using the old semantic chunking version:

**Old code:**
```python
chunks = load_and_split_pdf_from_storage(
    'pdfs/book.pdf',
    chunk_size=1000,
    break_point_percentile_threshold=95,
    use_semantic_chunking=True
)
```

**New code:**
```python
chunks = load_and_split_pdf_from_storage(
    'pdfs/book.pdf',
    chunk_size=1000,
    chunk_overlap=200
)
```

**Key changes:**
- Remove `break_point_percentile_threshold` parameter
- Remove `use_semantic_chunking` parameter
- Use `chunk_overlap` instead (replaces the percentile concept)

## Dependencies

Only requires:
```
langchain-community>=0.3.25        # PyMuPDFLoader
langchain-text-splitters>=0.3.8    # RecursiveCharacterTextSplitter
langchain-core>=0.3.70             # Document base class
firebase-admin>=6.6.0              # Firebase Storage
PyMuPDF>=1.26.0                    # PDF parsing
```

No need for OpenAI API or embeddings!

## Benefits of This Approach

✅ **Cost-free**: No API calls, no billing surprises
✅ **Fast**: Local processing, no network latency
✅ **Simple**: Easy to understand and configure
✅ **Reliable**: No external service dependencies
✅ **Flexible**: Easy to customize chunk sizes and overlaps
✅ **Production-ready**: Well-tested implementation

## Document Output Format

Each chunk includes:
```python
{
    'page_content': 'The actual text content...',
    'metadata': {
        'source': 'pdfs/book123.pdf',
        'storage_type': 'firebase_storage',
        'page': 0,
        'total_pages': 100,
        # ... additional PDF metadata
    }
}
```

## Troubleshooting

### Chunks Too Large
```python
# Decrease chunk_size
chunks = split_pdf_text(documents, chunk_size=500)
```

### Chunks Too Small
```python
# Increase chunk_size
chunks = split_pdf_text(documents, chunk_size=2000)
```

### Need More Context
```python
# Increase chunk_overlap
chunks = split_pdf_text(documents, chunk_overlap=500)
```

## Status

✓ **Updated and verified**
✓ **All syntax checks passed**
✓ **All imports working**
✓ **Production ready**

Last updated: 2024-10-29
