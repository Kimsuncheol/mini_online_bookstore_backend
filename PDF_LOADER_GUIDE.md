# PDF Loader Utility Guide

## Overview

The `app/utils/pdf_loader.py` module provides utility functions to load PDF files from Firebase Storage and split their text using LangChain's semantic chunking capabilities.

## Key Features

### 1. Firebase Storage Integration
- Direct integration with Firebase Storage buckets
- Automatic download and temporary file management
- Error handling for missing files

### 2. PDF Loading with PyMuPDFLoader
- Efficient PDF parsing using PyMuPDF
- Extracts page-by-page content as LangChain Documents
- Preserves metadata including page numbers and source information

### 3. Semantic Text Splitting
- Uses `SemanticChunker` from LangChain to intelligently split text
- Based on semantic similarity computed with OpenAI embeddings
- Finds natural breakpoints that maintain semantic coherence
- Configurable chunk size and percentile thresholds

## Dependencies

```
langchain-community>=0.3.25
langchain-experimental>=0.3.4
langchain-openai>=0.3.21
langchain-core>=0.3.70
langchain-text-splitters>=0.3.8
firebase-admin>=6.6.0
PyMuPDF>=1.26.0
```

All dependencies are already included in `requirements.txt`.

## API Reference

### Exception Classes

#### `PDFLoaderError`
Base exception for PDF loading operations.

#### `PDFNotFoundError`
Raised when a PDF file is not found in Firebase Storage.

#### `PDFProcessingError`
Raised when PDF loading or text splitting fails.

### Functions

#### `get_firebase_storage()`
Get Firebase Storage bucket instance.

**Returns:**
- `google.cloud.storage.bucket.Bucket`: Firebase Storage bucket

**Raises:**
- `PDFLoaderError`: If Firebase app is not initialized

```python
from app.utils.pdf_loader import get_firebase_storage

bucket = get_firebase_storage()
```

#### `download_pdf_from_storage(bucket_path, bucket_name=None)`
Download a PDF file from Firebase Storage.

**Parameters:**
- `bucket_path` (str): Path to the PDF file in Firebase Storage (e.g., `'pdfs/book123.pdf'`)
- `bucket_name` (Optional[str]): Firebase Storage bucket name (reserved for future use)

**Returns:**
- `bytes`: PDF file content as bytes

**Raises:**
- `PDFNotFoundError`: If the file doesn't exist
- `PDFLoaderError`: If download fails

```python
from app.utils.pdf_loader import download_pdf_from_storage

pdf_bytes = download_pdf_from_storage('pdfs/book123.pdf')
```

#### `load_pdf_from_storage(bucket_path, bucket_name=None)`
Load a PDF from Firebase Storage and extract its content as documents.

**Parameters:**
- `bucket_path` (str): Path to the PDF file in Firebase Storage
- `bucket_name` (Optional[str]): Firebase Storage bucket name

**Returns:**
- `List[Document]`: List of LangChain Document objects with page content and metadata

**Raises:**
- `PDFNotFoundError`: If the file doesn't exist
- `PDFProcessingError`: If PDF loading fails

```python
from app.utils.pdf_loader import load_pdf_from_storage

documents = load_pdf_from_storage('pdfs/book123.pdf')
for doc in documents:
    print(f"Page {doc.metadata.get('page')}: {doc.page_content[:100]}...")
```

#### `split_pdf_text(documents, chunk_size=1000, break_point_percentile_threshold=95, use_semantic_chunking=True)`
Split PDF text using semantic chunking.

**Parameters:**
- `documents` (List[Document]): List of documents from PDF loader
- `chunk_size` (int): Target chunk size in characters (default: 1000)
- `break_point_percentile_threshold` (int): Percentile threshold for determining semantic breakpoints (default: 95)
  - Higher values (closer to 100): Breaks only at very large semantic distances (larger chunks)
  - Lower values (closer to 0): Breaks more frequently (smaller chunks)
- `use_semantic_chunking` (bool): Whether to use semantic chunking. If False, uses basic character splitting (default: True)

**Returns:**
- `List[Document]`: List of split documents with semantic awareness

**Raises:**
- `PDFProcessingError`: If splitting fails

```python
from app.utils.pdf_loader import split_pdf_text

split_docs = split_pdf_text(documents, chunk_size=500, break_point_percentile_threshold=90)
print(f"Created {len(split_docs)} chunks")
```

#### `load_and_split_pdf_from_storage(bucket_path, bucket_name=None, chunk_size=1000, break_point_percentile_threshold=95, use_semantic_chunking=True)`
Load a PDF from Firebase Storage and split its text in one operation.

**Parameters:**
- `bucket_path` (str): Path to the PDF file in Firebase Storage
- `bucket_name` (Optional[str]): Firebase Storage bucket name
- `chunk_size` (int): Target chunk size in characters (default: 1000)
- `break_point_percentile_threshold` (int): Percentile threshold for semantic breaks (default: 95)
- `use_semantic_chunking` (bool): Whether to use semantic chunking (default: True)

**Returns:**
- `List[Document]`: List of split documents with metadata

**Raises:**
- `PDFNotFoundError`: If the PDF file doesn't exist
- `PDFProcessingError`: If loading or splitting fails

```python
from app.utils.pdf_loader import load_and_split_pdf_from_storage

chunks = load_and_split_pdf_from_storage(
    'pdfs/book123.pdf',
    chunk_size=800,
    break_point_percentile_threshold=90
)
print(f"Loaded and split PDF into {len(chunks)} semantic chunks")
```

#### `load_pdf_from_local_path(file_path)`
Load a PDF from a local file path.

Useful for development and testing without Firebase Storage dependency.

**Parameters:**
- `file_path` (str): Path to the PDF file on the local filesystem

**Returns:**
- `List[Document]`: List of LangChain Document objects

**Raises:**
- `PDFNotFoundError`: If the file doesn't exist
- `PDFProcessingError`: If PDF loading fails

```python
from app.utils.pdf_loader import load_pdf_from_local_path

documents = load_pdf_from_local_path('/path/to/document.pdf')
```

#### `load_and_split_pdf_from_local(file_path, chunk_size=1000, break_point_percentile_threshold=95, use_semantic_chunking=True)`
Load a PDF from local filesystem and split its text in one operation.

**Parameters:**
- `file_path` (str): Path to the PDF file on the local filesystem
- `chunk_size` (int): Target chunk size in characters (default: 1000)
- `break_point_percentile_threshold` (int): Percentile threshold for semantic breaks (default: 95)
- `use_semantic_chunking` (bool): Whether to use semantic chunking (default: True)

**Returns:**
- `List[Document]`: List of split documents with metadata

**Raises:**
- `PDFNotFoundError`: If the PDF file doesn't exist
- `PDFProcessingError`: If loading or splitting fails

```python
from app.utils.pdf_loader import load_and_split_pdf_from_local

chunks = load_and_split_pdf_from_local('/path/to/document.pdf')
```

## Usage Examples

### Example 1: Simple PDF Loading from Firebase Storage

```python
from app.utils.pdf_loader import load_pdf_from_storage

try:
    # Load PDF from Firebase Storage
    documents = load_pdf_from_storage('books/python_guide.pdf')

    # Iterate through pages
    for doc in documents:
        print(f"Page {doc.metadata.get('page')}: {len(doc.page_content)} characters")

except PDFNotFoundError:
    print("PDF not found in Firebase Storage")
except PDFProcessingError as e:
    print(f"Error loading PDF: {e}")
```

### Example 2: Load and Split with Semantic Chunking

```python
from app.utils.pdf_loader import load_and_split_pdf_from_storage

try:
    # Load and split in one operation
    chunks = load_and_split_pdf_from_storage(
        'books/technical_manual.pdf',
        chunk_size=1500,
        break_point_percentile_threshold=90,
        use_semantic_chunking=True
    )

    # Each chunk is semantically coherent
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: {len(chunk.page_content)} characters")

except Exception as e:
    print(f"Error: {e}")
```

### Example 3: Local Development Testing

```python
from app.utils.pdf_loader import load_and_split_pdf_from_local

try:
    # Test locally without Firebase
    chunks = load_and_split_pdf_from_local(
        './test_documents/sample.pdf',
        chunk_size=1000
    )

    print(f"Created {len(chunks)} chunks")

except Exception as e:
    print(f"Error: {e}")
```

### Example 4: Custom Chunk Parameters

```python
from app.utils.pdf_loader import load_pdf_from_storage, split_pdf_text

try:
    # Load PDF
    documents = load_pdf_from_storage('books/technical_manual.pdf')

    # First, try with conservative splitting
    conservative_chunks = split_pdf_text(
        documents,
        chunk_size=2000,
        break_point_percentile_threshold=98,  # Very selective about breaks
        use_semantic_chunking=True
    )

    # Or use basic splitting for speed
    basic_chunks = split_pdf_text(
        documents,
        chunk_size=1000,
        use_semantic_chunking=False  # Simple character splitting
    )

    print(f"Conservative: {len(conservative_chunks)} chunks")
    print(f"Basic: {len(basic_chunks)} chunks")

except Exception as e:
    print(f"Error: {e}")
```

## Document Metadata

When documents are loaded, they include the following metadata:

```python
{
    'source': 'pdfs/book123.pdf',              # Original source path
    'storage_type': 'firebase_storage',        # 'firebase_storage' or 'local'
    'page': 0,                                 # Page number (0-indexed)
    'total_pages': 10,                         # Total pages in document
    # ... other PyMuPDF metadata
}
```

## Semantic Chunking Configuration

### Understanding `break_point_percentile_threshold`

The `break_point_percentile_threshold` parameter controls how aggressively the semantic chunker breaks the text:

- **95 (default)**: Breaks at the 95th percentile of semantic distances
  - Conservative approach: larger, more coherent chunks
  - Recommended for most use cases

- **90**: More aggressive breaking
  - Medium-sized chunks with good coherence
  - Good balance between size and semantic quality

- **75**: Very aggressive breaking
  - Smaller chunks
  - May split at less significant boundaries

- **98+**: Very conservative breaking
  - Large chunks
  - Only breaks at major topic changes

### Chunk Size vs. Semantic Coherence

- **Larger chunk_size**: Fewer, larger chunks (but may exceed the target)
- **Smaller chunk_size**: More, smaller chunks (semantic chunker respects this as a guideline)

The semantic chunker uses both parameters together:
1. First, it attempts to respect the `chunk_size` target
2. Then, it adjusts boundaries based on semantic similarity thresholds

## Performance Considerations

### Processing Time

- **PDF Download**: Depends on file size and network (Firebase optimized)
- **PDF Parsing**: ~100ms per page with PyMuPDFLoader
- **Semantic Chunking**: Requires OpenAI embeddings API calls (costs money!)
  - Typical: 50-100ms per chunk
  - Budget accordingly for production use

### Cost (Semantic Chunking)

Semantic chunking uses OpenAI embeddings:
- Cost: ~$0.02 per 1M input tokens (as of 2024)
- For a 100-page document split into 200 chunks: ~$0.01-0.02 per document

### Optimization Tips

1. **Use basic splitting for preview**: Set `use_semantic_chunking=False` for quick previews
2. **Batch process**: If processing many documents, batch the embedding API calls
3. **Cache chunks**: Store split results in Firestore to avoid re-processing
4. **Adjust percentile**: Use higher thresholds (98+) to create larger chunks and reduce API calls

## Error Handling

```python
from app.utils.pdf_loader import (
    load_and_split_pdf_from_storage,
    PDFNotFoundError,
    PDFProcessingError,
    PDFLoaderError
)

try:
    chunks = load_and_split_pdf_from_storage('pdfs/book.pdf')
except PDFNotFoundError:
    # Handle missing file
    print("PDF not found in storage")
except PDFProcessingError:
    # Handle processing errors (corrupt PDF, encoding issues)
    print("PDF processing failed")
except PDFLoaderError:
    # Handle Firebase storage errors
    print("Storage access error")
except Exception as e:
    # Handle unexpected errors
    print(f"Unexpected error: {e}")
```

## Troubleshooting

### "Firebase app not initialized"
- Ensure `init_firebase()` is called in your application startup
- Check that Firebase credentials are properly configured

### "PDF file not found in Firebase Storage"
- Verify the `bucket_path` is correct
- Check that the file exists in Firebase Storage
- Ensure the Firebase app has read permissions

### OpenAI API Errors
- Verify `OPENAI_API_KEY` environment variable is set
- Check API quota and billing status
- May occur due to large documents or API rate limits

### Memory Issues with Large PDFs
- The module uses temporary files, so large PDFs should be manageable
- If issues persist, consider processing PDFs in smaller sections

## Related Files

- [firebase_config.py](app/utils/firebase_config.py) - Firebase initialization
- [book_viewer_service.py](app/services/book_viewer_service.py) - Existing PDF handling for viewing

## Future Enhancements

- [ ] Custom bucket support (bucket_name parameter)
- [ ] Async/parallel processing for multiple PDFs
- [ ] Caching layer for split chunks
- [ ] Alternative embedding models (local, Azure, etc.)
- [ ] PDF preprocessing (OCR, layout analysis)
