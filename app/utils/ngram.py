"""
N-gram Utility Module

Provides functions for generating n-grams from text for search indexing and analysis.
N-grams are contiguous sequences of n items from a given sample of text.

Uses:
- Text-based search and indexing
- Fuzzy matching and typo tolerance
- Content-based similarity analysis
"""

from typing import List, Set, Tuple
import re


def normalize_text(text: str) -> str:
    """
    Normalize text for n-gram generation.

    Args:
        text: Raw text to normalize

    Returns:
        Normalized text (lowercase, whitespace trimmed)
    """
    if not text:
        return ""
    return text.lower().strip()


def tokenize(text: str, lowercase: bool = True) -> List[str]:
    """
    Tokenize text into words.

    Args:
        text: Text to tokenize
        lowercase: Whether to convert to lowercase

    Returns:
        List of tokens
    """
    if not text:
        return []

    if lowercase:
        text = text.lower()

    # Split by whitespace and remove punctuation
    tokens = re.findall(r'\b\w+\b', text)
    return tokens


def generate_character_ngrams(text: str, n: int = 3) -> Set[str]:
    """
    Generate character-level n-grams from text.

    Character n-grams are useful for fuzzy matching and typo tolerance.

    Args:
        text: Input text
        n: Size of n-grams (default: 3 for trigrams)

    Returns:
        Set of unique character n-grams

    Example:
        >>> generate_character_ngrams("hello", 2)
        {'he', 'el', 'll', 'lo'}
    """
    text = normalize_text(text)

    if len(text) < n:
        return {text}

    ngrams = set()
    for i in range(len(text) - n + 1):
        ngrams.add(text[i:i + n])

    return ngrams


def generate_word_ngrams(text: str, n: int = 2) -> Set[str]:
    """
    Generate word-level n-grams from text.

    Word n-grams preserve semantic meaning better than character n-grams.

    Args:
        text: Input text
        n: Size of n-grams (default: 2 for bigrams)

    Returns:
        Set of unique word n-grams

    Example:
        >>> generate_word_ngrams("the quick brown fox", 2)
        {'the quick', 'quick brown', 'brown fox'}
    """
    tokens = tokenize(text)

    if len(tokens) < n:
        return {" ".join(tokens)} if tokens else set()

    ngrams = set()
    for i in range(len(tokens) - n + 1):
        ngrams.add(" ".join(tokens[i:i + n]))

    return ngrams


def generate_mixed_ngrams(text: str, char_n: int = 3, word_n: int = 2) -> dict:
    """
    Generate both character and word n-grams from text.

    Args:
        text: Input text
        char_n: Character n-gram size
        word_n: Word n-gram size

    Returns:
        Dictionary with 'char_ngrams' and 'word_ngrams' keys
    """
    return {
        "char_ngrams": generate_character_ngrams(text, char_n),
        "word_ngrams": generate_word_ngrams(text, word_n),
    }


def jaccard_similarity(ngrams1: Set[str], ngrams2: Set[str]) -> float:
    """
    Calculate Jaccard similarity between two sets of n-grams.

    Jaccard similarity = |intersection| / |union|

    Args:
        ngrams1: First set of n-grams
        ngrams2: Second set of n-grams

    Returns:
        Similarity score between 0 and 1
    """
    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = len(ngrams1 & ngrams2)
    union = len(ngrams1 | ngrams2)

    return intersection / union if union > 0 else 0.0


def calculate_string_similarity(text1: str, text2: str, ngram_type: str = "char", n: int = 3) -> float:
    """
    Calculate similarity between two strings using n-gram analysis.

    Args:
        text1: First string
        text2: Second string
        ngram_type: Type of n-grams ('char' or 'word')
        n: Size of n-grams

    Returns:
        Similarity score between 0 and 1
    """
    if ngram_type == "char":
        ngrams1 = generate_character_ngrams(text1, n)
        ngrams2 = generate_character_ngrams(text2, n)
    else:
        ngrams1 = generate_word_ngrams(text1, n)
        ngrams2 = generate_word_ngrams(text2, n)

    return jaccard_similarity(ngrams1, ngrams2)


def find_similar_strings(query: str, candidates: List[str],
                        threshold: float = 0.5,
                        ngram_type: str = "char",
                        n: int = 3) -> List[Tuple[str, float]]:
    """
    Find strings similar to a query using n-gram analysis.

    Args:
        query: Search query
        candidates: List of candidate strings to compare
        threshold: Minimum similarity score (0-1)
        ngram_type: Type of n-grams ('char' or 'word')
        n: Size of n-grams

    Returns:
        List of tuples (candidate, similarity_score) sorted by score descending
    """
    results = []

    for candidate in candidates:
        similarity = calculate_string_similarity(query, candidate, ngram_type, n)

        if similarity >= threshold:
            results.append((candidate, similarity))

    # Sort by similarity score descending
    results.sort(key=lambda x: x[1], reverse=True)

    return results


def build_search_index(items: List[str], ngram_type: str = "char", n: int = 3) -> dict:
    """
    Build an n-gram index for faster fuzzy search.

    Args:
        items: List of strings to index
        ngram_type: Type of n-grams ('char' or 'word')
        n: Size of n-grams

    Returns:
        Dictionary mapping n-grams to list of item indices

    Example:
        >>> index = build_search_index(["apple", "application", "apply"])
        >>> index["app"] # Will contain indices of items with "app" n-gram
    """
    index = {}

    for item_idx, item in enumerate(items):
        if ngram_type == "char":
            ngrams = generate_character_ngrams(item, n)
        else:
            ngrams = generate_word_ngrams(item, n)

        for ngram in ngrams:
            if ngram not in index:
                index[ngram] = []
            index[ngram].append(item_idx)

    return index


def search_using_index(query: str, index: dict, items: List[str],
                      ngram_type: str = "char", n: int = 3) -> List[Tuple[str, float]]:
    """
    Perform fuzzy search using pre-built n-gram index.

    More efficient than searching all candidates when index is reused.

    Args:
        query: Search query
        index: Pre-built n-gram index from build_search_index()
        items: Original list of indexed items
        ngram_type: Type of n-grams ('char' or 'word')
        n: Size of n-grams

    Returns:
        List of matching items with similarity scores
    """
    # Get n-grams from query
    if ngram_type == "char":
        query_ngrams = generate_character_ngrams(query, n)
    else:
        query_ngrams = generate_word_ngrams(query, n)

    # Find candidate items that share n-grams with query
    candidate_indices = set()
    for ngram in query_ngrams:
        if ngram in index:
            candidate_indices.update(index[ngram])

    # Calculate similarity for candidates only
    results = []
    for idx in candidate_indices:
        similarity = calculate_string_similarity(query, items[idx], ngram_type, n)
        results.append((items[idx], similarity))

    # Sort by similarity
    results.sort(key=lambda x: x[1], reverse=True)

    return results
