"""Mock Firestore client for testing with file-based persistence."""

import copy
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List


# ISO 8601 datetime pattern for detecting datetime strings
DATETIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?$"
)


def datetime_to_json(obj: Any) -> Any:
    """Convert datetime objects to ISO format strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def parse_datetime_strings(data: Any) -> Any:
    """
    Recursively parse ISO datetime strings back to datetime objects.

    Handles:
    - ISO 8601 strings (with or without timezone, with or without microseconds)
    - Nested dictionaries and lists
    - Preserves non-datetime strings
    """
    if isinstance(data, dict):
        return {key: parse_datetime_strings(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [parse_datetime_strings(item) for item in data]
    elif isinstance(data, str) and DATETIME_PATTERN.match(data):
        try:
            # Try parsing with timezone info first
            if "+" in data or data.endswith("Z"):
                return datetime.fromisoformat(data.replace("Z", "+00:00"))
            # Try parsing space-separated format (common in our data)
            elif " " in data:
                # Handle format: "2025-11-09 10:30:00" or "2025-11-09 10:30:00.123456"
                return datetime.fromisoformat(data)
            else:
                return datetime.fromisoformat(data)
        except (ValueError, AttributeError):
            # Not a valid datetime, return as-is
            return data
    return data


class Increment:
    """Mock for Firestore.Increment()."""

    def __init__(self, value: int = 1):
        self.value = value


# Make it accessible as firestore.Increment for compatibility
class firestore:
    """Mock firestore module."""

    Increment = Increment

    class Query:
        ASCENDING = "ASCENDING"
        DESCENDING = "DESCENDING"


class MockDocument:
    """Mock Firestore document."""

    def __init__(
        self, data: Dict[str, Any] | None = None, exists: bool = True, doc_id: str | None = None, reference: "MockDocumentReference | None" = None
    ):
        self._data = data or {}
        self._exists = exists
        self.id = doc_id or self._data.get("session_id") or self._data.get("id", "mock_id")
        self.reference = reference  # Back-reference to the document reference

    @property
    def exists(self) -> bool:
        return self._exists

    def to_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data)

    def get(self, field: str) -> Any:
        return self._data.get(field)


class MockDocumentReference:
    """Mock Firestore document reference."""

    def __init__(self, path: str, storage: Dict[str, Any], on_change=None):
        self.path = path
        self._storage = storage
        self._on_change = on_change  # Callback to trigger persistence
        self.id = path.split("/")[-1]

    async def get(self, transaction=None) -> MockDocument:
        """Get document (optionally in transaction context)."""
        data = self._storage.get(self.path)
        return MockDocument(data, exists=data is not None, reference=self)

    async def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        if merge and self.path in self._storage:
            self._storage[self.path].update(data)
        else:
            self._storage[self.path] = copy.deepcopy(data)
        if self._on_change:
            self._on_change()  # Trigger save to disk

    async def update(self, data: Dict[str, Any]) -> None:
        # Import google.cloud.firestore if available to handle both mock and real Increment
        try:
            from google.cloud import firestore as gcp_firestore

            real_increment = gcp_firestore.Increment
        except ImportError:
            real_increment = None

        if self.path in self._storage:
            # Handle Firestore.Increment (both mock and real)
            updated_data = {}
            for key, value in data.items():
                if isinstance(value, Increment):
                    # Apply mock increment to existing value
                    current_value = self._storage[self.path].get(key, 0)
                    updated_data[key] = current_value + value.value
                elif real_increment and isinstance(value, real_increment):
                    # Apply real Firestore increment to existing value
                    current_value = self._storage[self.path].get(key, 0)
                    # Real Increment has a private _value attribute
                    inc_value = getattr(value, "_value", 1)
                    updated_data[key] = current_value + inc_value
                else:
                    updated_data[key] = value
            self._storage[self.path].update(updated_data)
        else:
            # Handle Increment in new documents
            new_data = {}
            for key, value in data.items():
                if isinstance(value, Increment):
                    new_data[key] = value.value  # Initialize to increment value
                elif real_increment and isinstance(value, real_increment):
                    # Real Increment has a private _value attribute
                    inc_value = getattr(value, "_value", 1)
                    new_data[key] = inc_value
                else:
                    new_data[key] = value
            self._storage[self.path] = new_data
        if self._on_change:
            self._on_change()  # Trigger save to disk

    async def delete(self) -> None:
        if self.path in self._storage:
            del self._storage[self.path]
        if self._on_change:
            self._on_change()  # Trigger save to disk

    def collection(self, name: str) -> "MockCollectionReference":
        return MockCollectionReference(f"{self.path}/{name}", self._storage, self._on_change)


class MockCollectionReference:
    """Mock Firestore collection reference."""

    _filters: list[tuple[str, str, Any]]
    _order_by: tuple[str, str] | None
    _limit_count: int | None
    _limit_to_last: int | None

    def __init__(self, path: str, storage: Dict[str, Any], on_change=None):
        self.path = path
        self._storage = storage
        self._on_change = on_change  # Callback to trigger persistence
        self._filters = []
        self._order_by = None
        self._limit_count = None
        self._limit_to_last = None

    def document(self, doc_id: str | None = None) -> MockDocumentReference:
        if doc_id is None:
            doc_id = f"mock_{len(self._storage)}"
        return MockDocumentReference(f"{self.path}/{doc_id}", self._storage, self._on_change)

    def where(self, field: str, op: str, value: Any) -> "MockCollectionReference":
        """Add a filter to the query."""
        self._filters.append((field, op, value))
        return self

    def _apply_filter(self, data: Dict[str, Any], field: str, op: str, value: Any) -> bool:
        """Apply a single filter to check if data matches."""
        # Handle nested fields (e.g., "metadata.session_type")
        if "." in field:
            parts = field.split(".")
            field_value = data
            for part in parts:
                if isinstance(field_value, dict):
                    field_value = field_value.get(part)
                else:
                    field_value = None
                    break
        else:
            field_value = data.get(field)

        if op == "==":
            return field_value == value
        elif op == "!=":
            return field_value != value
        elif op == ">":
            return field_value is not None and field_value > value
        elif op == ">=":
            return field_value is not None and field_value >= value
        elif op == "<":
            return field_value is not None and field_value < value
        elif op == "<=":
            return field_value is not None and field_value <= value
        elif op == "in":
            return field_value in value
        elif op == "not-in":
            return field_value not in value
        elif op == "array-contains":
            return isinstance(field_value, list) and value in field_value
        else:
            # Unknown operator, default to ==
            return field_value == value

    def order_by(self, field: str, direction: str = "ASCENDING") -> "MockCollectionReference":
        self._order_by = (field, direction)
        return self

    def limit(self, count: int) -> "MockCollectionReference":
        self._limit_count = count
        return self

    async def get(self) -> List[MockDocument]:
        results = []

        for path, data in self._storage.items():
            if path.startswith(self.path + "/") and path.count("/") == self.path.count("/") + 1:
                matches = True
                for field, op, value in self._filters:
                    if not self._apply_filter(data, field, op, value):
                        matches = False
                        break

                if matches:
                    doc_id = path.split("/")[-1]
                    # Create a reference so callers can use doc.reference.delete()
                    doc_ref = MockDocumentReference(path, self._storage, self._on_change)
                    results.append(MockDocument(data, doc_id=doc_id, reference=doc_ref))

        if self._order_by:
            field, direction = self._order_by
            reverse = direction == "DESCENDING"

            # Separate None and non-None values to ensure None always at end
            none_docs = [doc for doc in results if doc.to_dict().get(field) is None]
            value_docs = [doc for doc in results if doc.to_dict().get(field) is not None]

            # Sort only the non-None values
            value_docs.sort(key=lambda d: d.to_dict().get(field), reverse=reverse)

            # Combine: non-None first, then None at the end
            results = value_docs + none_docs

        if self._limit_count:
            results = results[: self._limit_count]

        return results

    async def stream(self):
        """Async generator yielding documents (matches real Firestore async behavior)."""
        # Filter documents
        results = []
        for path, data in self._storage.items():
            if path.startswith(self.path + "/") and path.count("/") == self.path.count("/") + 1:
                matches = True
                for field, op, value in self._filters:
                    if not self._apply_filter(data, field, op, value):
                        matches = False
                        break

                if matches:
                    # Extract doc_id from path for proper document ID
                    doc_id = path.split("/")[-1]
                    # Create a reference so callers can use doc.reference.delete()
                    doc_ref = MockDocumentReference(path, self._storage, self._on_change)
                    results.append(MockDocument(data, doc_id=doc_id, reference=doc_ref))

        if self._order_by:
            field, direction = self._order_by
            reverse = direction == "DESCENDING"

            # Separate None and non-None values to ensure None always at end
            none_docs = [doc for doc in results if doc.to_dict().get(field) is None]
            value_docs = [doc for doc in results if doc.to_dict().get(field) is not None]

            # Sort only the non-None values
            value_docs.sort(key=lambda d: d.to_dict().get(field), reverse=reverse)

            # Combine: non-None first, then None at the end
            results = value_docs + none_docs

        if self._limit_count:
            results = results[: self._limit_count]

        for doc in results:
            yield doc

    def limit_to_last(self, count: int) -> "MockCollectionReference":
        """Limit results from the end."""
        # For mock, we'll just store this and handle in get()
        self._limit_to_last = count
        return self

    async def add(self, data: Dict[str, Any]) -> MockDocumentReference:
        doc_id = f"mock_{len(self._storage)}"
        doc_ref = self.document(doc_id)
        await doc_ref.set(data)
        return doc_ref


class MockTransaction:
    """Mock Firestore transaction."""

    def __init__(self, storage: Dict[str, Any], on_change=None):
        self._storage = storage
        self._on_change = on_change
        self._read_only = False
        self._max_attempts = 5
        self._rolled_back = False
        self._rollback = False  # Add this for compatibility
        self._write_pbs: list[Any] = []
        self._id = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._do_rollback()
        return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._do_rollback()
        return False

    def _do_rollback(self):
        """Mark transaction as rolled back."""
        self._rolled_back = True
        self._rollback = True  # Set both for compatibility

    def _clean_up(self):
        """Clean up transaction state."""
        self._write_pbs = []
        self._id = None

    def _begin(self, retry_id=None):
        """Begin transaction (Firestore internal)."""
        pass

    def _commit(self):
        """Commit transaction (Firestore internal)."""
        pass

    def set(self, doc_ref: MockDocumentReference, data: Dict[str, Any], merge: bool = False):
        """Set document data in transaction."""
        if merge and doc_ref.path in self._storage:
            self._storage[doc_ref.path].update(data)
        else:
            self._storage[doc_ref.path] = copy.deepcopy(data)
        if self._on_change:
            self._on_change()

    def update(self, doc_ref: MockDocumentReference, data: Dict[str, Any]):
        """Update document data in transaction."""
        if doc_ref.path in self._storage:
            self._storage[doc_ref.path].update(data)
        else:
            self._storage[doc_ref.path] = copy.deepcopy(data)
        if self._on_change:
            self._on_change()

    def delete(self, doc_ref: MockDocumentReference):
        """Delete document in transaction."""
        if doc_ref.path in self._storage:
            del self._storage[doc_ref.path]
        if self._on_change:
            self._on_change()

    def get(self, ref):
        """Get document in transaction context."""
        return ref.get()

    async def get_async(self, ref):
        """Async get document in transaction context."""
        return await ref.get()


class MockFirestoreClient:
    """Mock Firestore client with file-based persistence."""

    def __init__(self, persist_path: str | None = None):
        """Initialize mock Firestore with optional file persistence.

        Args:
            persist_path: Path to JSON file for persisting data. If None, uses in-memory only.
        """
        self._persist_path = persist_path or ".firestore_mock_data.json"
        self._storage: Dict[str, Any] = {}
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load data from disk if persistence file exists."""
        if os.path.exists(self._persist_path):
            try:
                with open(self._persist_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                # Parse datetime strings back to datetime objects
                self._storage = {
                    key: parse_datetime_strings(value) for key, value in raw_data.items()
                }
                print(f"[LOAD] Loaded {len(self._storage)} documents from {self._persist_path}")
            except Exception as e:
                print(f"[WARN] Failed to load mock Firestore data: {e}")
                self._storage = {}

    def _save_to_disk(self) -> None:
        """Save data to disk for persistence with datetime serialization."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self._persist_path)), exist_ok=True)

            with open(self._persist_path, "w", encoding="utf-8") as f:
                json.dump(self._storage, f, indent=2, default=datetime_to_json)
        except Exception as e:
            print(f"[WARN] Failed to save mock Firestore data: {e}")

    def collection(self, path: str) -> MockCollectionReference:
        return MockCollectionReference(path, self._storage, on_change=self._save_to_disk)

    def document(self, path: str) -> MockDocumentReference:
        return MockDocumentReference(path, self._storage, on_change=self._save_to_disk)

    async def close(self) -> None:
        """Save data on close."""
        self._save_to_disk()

    def seed_data(self, collection: str, doc_id: str, data: Dict[str, Any]) -> None:
        """Seed test data into mock storage."""
        path = f"{collection}/{doc_id}"
        self._storage[path] = copy.deepcopy(data)
        self._save_to_disk()

    def transaction(self):
        """Return mock transaction context manager."""
        return MockTransaction(self._storage, on_change=self._save_to_disk)
