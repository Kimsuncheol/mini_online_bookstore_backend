"""
Mock Firestore implementation for local development and testing.

This lightweight, in-memory Firestore mock supports the subset of features
used by the project's services, including:
- Collections, documents, and nested subcollections
- Auto-generated document IDs
- Basic querying with where/limit
- Document set, update, delete, and get operations

It enables running the application without real Firebase credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple
from uuid import uuid4
import copy


def _matches_filter(value: Any, operator: str, expected: Any) -> bool:
    """Evaluate a single filter comparison."""
    if operator == "==":
        return value == expected
    if operator == "!=":
        return value != expected
    if operator == "<":
        return value is not None and value < expected
    if operator == "<=":
        return value is not None and value <= expected
    if operator == ">":
        return value is not None and value > expected
    if operator == ">=":
        return value is not None and value >= expected
    raise ValueError(f"Unsupported operator '{operator}'")


@dataclass
class MockDocumentSnapshot:
    """Represents a document snapshot."""

    id: str
    data: Optional[Dict[str, Any]]
    reference: "MockDocumentReference"

    @property
    def exists(self) -> bool:
        return self.data is not None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        if self.data is None:
            return None
        return copy.deepcopy(self.data)


class MockDocumentReference:
    """Reference to a document within a collection."""

    def __init__(self, collection: "MockCollectionReference", doc_id: str):
        self._collection = collection
        self.id = doc_id

    def get(self) -> MockDocumentSnapshot:
        store = self._collection._get_document_store(self.id, create=False)
        data = None if store is None else store["fields"]
        return MockDocumentSnapshot(self.id, copy.deepcopy(data) if data else data, self)

    def set(self, data: Dict[str, Any]) -> None:
        store = self._collection._get_document_store(self.id, create=True)
        store["fields"] = copy.deepcopy(data)

    def update(self, data: Dict[str, Any]) -> None:
        store = self._collection._get_document_store(self.id, create=False)
        if store is None:
            raise ValueError(f"Document '{self.id}' does not exist.")
        store["fields"].update(copy.deepcopy(data))

    def delete(self) -> None:
        self._collection._delete_document(self.id)

    def collection(self, name: str) -> "MockCollectionReference":
        store = self._collection._get_document_store(self.id, create=True)
        subcollections = store["subcollections"]
        sub_store = subcollections.setdefault(name, {})
        return MockCollectionReference(
            self._collection._db,
            f"{self._collection._name}/{self.id}/{name}",
            sub_store,
            parent=self,
        )


class MockQuery:
    """Represents a query built from collection filters."""

    def __init__(
        self,
        collection: "MockCollectionReference",
        filters: Optional[List[Tuple[str, str, Any]]] = None,
        limit_value: Optional[int] = None,
    ):
        self._collection = collection
        self._filters = filters or []
        self._limit = limit_value

    def where(self, field: str, operator: str, value: Any) -> "MockQuery":
        return MockQuery(
            self._collection,
            filters=self._filters + [(field, operator, value)],
            limit_value=self._limit,
        )

    def limit(self, value: int) -> "MockQuery":
        return MockQuery(self._collection, filters=self._filters, limit_value=value)

    def stream(self) -> Iterator[MockDocumentSnapshot]:
        count = 0
        for snapshot in self._collection._iter_documents():
            data = snapshot.data
            if data is None:
                continue

            matches = True
            for field, operator, expected in self._filters:
                if not _matches_filter(data.get(field), operator, expected):
                    matches = False
                    break

            if not matches:
                continue

            yield snapshot

            if self._limit is not None:
                count += 1
                if count >= self._limit:
                    break


class MockCollectionReference:
    """Collection reference containing document stores."""

    def __init__(
        self,
        db: "MockFirestore",
        name: str,
        documents: Dict[str, Dict[str, Any]],
        parent: Optional[MockDocumentReference] = None,
    ):
        self._db = db
        self._name = name
        self._documents = documents
        self._parent = parent

    def document(self, doc_id: Optional[str] = None) -> MockDocumentReference:
        if doc_id is None:
            doc_id = uuid4().hex
        # Ensure store exists so nested collections can be created before set()
        self._get_document_store(doc_id, create=True)
        return MockDocumentReference(self, doc_id)

    def stream(self) -> Iterator[MockDocumentSnapshot]:
        yield from self._iter_documents()

    def where(self, field: str, operator: str, value: Any) -> MockQuery:
        return MockQuery(self, filters=[(field, operator, value)])

    def limit(self, value: int) -> MockQuery:
        return MockQuery(self, limit_value=value)

    # Internal helpers -------------------------------------------------
    def _get_document_store(self, doc_id: str, create: bool) -> Optional[Dict[str, Any]]:
        store = self._documents.get(doc_id)
        if store is None and create:
            store = {"fields": {}, "subcollections": {}}
            self._documents[doc_id] = store
        return store

    def _delete_document(self, doc_id: str) -> None:
        self._documents.pop(doc_id, None)

    def _iter_documents(self) -> Iterator[MockDocumentSnapshot]:
        for doc_id, store in list(self._documents.items()):
            fields = copy.deepcopy(store.get("fields") or None)
            yield MockDocumentSnapshot(
                doc_id,
                fields,
                MockDocumentReference(self, doc_id),
            )


class MockFirestore:
    """In-memory Firestore replacement."""

    def __init__(self):
        self._collections: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def collection(self, name: str) -> MockCollectionReference:
        documents = self._collections.setdefault(name, {})
        return MockCollectionReference(self, name, documents)
