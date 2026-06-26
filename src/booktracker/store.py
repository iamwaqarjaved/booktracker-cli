"""
store.py
--------
JSON-backed persistence for ReadingList.

Concepts demonstrated
~~~~~~~~~~~~~~~~~~~~~
- File I/O (json.load / json.dump)
- Error handling (FileNotFoundError, json.JSONDecodeError, PermissionError)
- Logging
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from booktracker.models import AudioBook, Book, ReadingList

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path.home() / ".booktracker" / "books.json"


class Store:
    """Loads and saves a ReadingList to a JSON file."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_PATH

    # ── public API ─────────────────────────────
    def load(self) -> ReadingList:
        """Read the JSON file and return a populated ReadingList."""
        rl = ReadingList()
        if not self.path.exists():
            logger.debug("Store file not found at %s — starting fresh.", self.path)
            return rl
        try:
            raw = self.path.read_text(encoding="utf-8").strip()
            if not raw:
                return rl
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Corrupt store file at {self.path}: {exc}"
            ) from exc
        except PermissionError as exc:
            raise PermissionError(
                f"Cannot read store file {self.path}: {exc}"
            ) from exc

        for item in data.get("books", []):
            if item.get("_type") == "audiobook":
                book = AudioBook.from_dict(item)
            else:
                book = Book.from_dict(item)
            rl.add(book)

        logger.info("Loaded %d book(s) from %s", len(rl), self.path)
        return rl

    def save(self, reading_list: ReadingList) -> None:
        """Serialise the ReadingList and write to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"books": [b.to_dict() for b in reading_list]}
        try:
            with self.path.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
        except PermissionError as exc:
            raise PermissionError(
                f"Cannot write store file {self.path}: {exc}"
            ) from exc
        logger.info("Saved %d book(s) to %s", len(reading_list), self.path)
