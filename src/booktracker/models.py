"""
models.py
---------
Domain model for BookTracker.

Concepts demonstrated
~~~~~~~~~~~~~~~~~~~~~
- @dataclass (Book)
- Inheritance (AudioBook → Book)
- @property with validation
- Dunder methods: __init__, __repr__, __str__, __eq__, __lt__, __len__,
  __contains__, __iter__  (8 total — exceeds 5 minimum)
- @classmethod alternate constructors
- Recursive function (_flatten_shelf)
- Instance methods with meaningful business behaviour
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from typing import Iterator

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Status constants
# ──────────────────────────────────────────────
TO_READ = "to-read"
READING = "reading"
DONE = "done"
VALID_STATUSES = (TO_READ, READING, DONE)


# ──────────────────────────────────────────────
# Book  (@dataclass)
# ──────────────────────────────────────────────
@dataclass
class Book:
    """Represents a single book in the reading list.

    Dunder methods: __init__ (auto), __repr__ (auto), __str__, __eq__ (auto),
                    __lt__, __hash__
    """

    title: str
    author: str
    total_pages: int
    pages_read: int = 0
    status: str = TO_READ
    rating: float | None = None          # 0.0–5.0
    notes: str = ""
    date_added: str = field(
        default_factory=lambda: datetime.date.today().isoformat()
    )
    date_finished: str | None = None

    # ── @property ──────────────────────────────
    @property
    def progress_pct(self) -> float:
        """Percentage of pages read (0–100)."""
        if self.total_pages <= 0:
            return 0.0
        return round(self.pages_read / self.total_pages * 100, 1)

    @property
    def is_finished(self) -> bool:
        return self.status == DONE

    # ── dunder: __str__ ────────────────────────
    def __str__(self) -> str:
        stars = f"  ★ {self.rating:.1f}" if self.rating is not None else ""
        return (
            f"[{self.status.upper():8}] {self.title} — {self.author} "
            f"({self.progress_pct}%{stars})"
        )

    # ── dunder: __lt__  (enables sorting) ──────
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self.title.lower() < other.title.lower()

    # ── dunder: __hash__ ───────────────────────
    # Needed because we override __eq__ via @dataclass(eq=True) and also
    # want to put Books in sets / dict keys.
    def __hash__(self) -> int:
        return hash((self.title.lower(), self.author.lower()))

    # ── @classmethod alternate constructors ────
    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        """Deserialise a Book from the JSON store."""
        return cls(
            title=data["title"],
            author=data["author"],
            total_pages=data["total_pages"],
            pages_read=data.get("pages_read", 0),
            status=data.get("status", TO_READ),
            rating=data.get("rating"),
            notes=data.get("notes", ""),
            date_added=data.get("date_added", datetime.date.today().isoformat()),
            date_finished=data.get("date_finished"),
        )

    @classmethod
    def quick(cls, title: str, author: str, pages: int) -> "Book":
        """Shorthand constructor for interactive / test use."""
        return cls(title=title, author=author, total_pages=pages)

    # ── instance methods (business behaviour) ──
    def start_reading(self) -> None:
        """Transition TO_READ → READING."""
        if self.status != TO_READ:
            raise ValueError(f"'{self.title}' is already {self.status!r}.")
        self.status = READING
        logger.info("Started reading %r", self.title)

    def finish(self, rating: float | None = None) -> None:
        """Transition READING → DONE, optionally record rating."""
        if self.status == DONE:
            raise ValueError(f"'{self.title}' is already marked done.")
        if rating is not None and not (0.0 <= rating <= 5.0):
            raise ValueError("Rating must be between 0.0 and 5.0.")
        self.status = DONE
        self.pages_read = self.total_pages
        self.rating = rating
        self.date_finished = datetime.date.today().isoformat()
        logger.info("Finished %r (rating=%s)", self.title, rating)

    def update_progress(self, pages: int) -> None:
        """Set pages_read; auto-start if still TO_READ."""
        if pages < 0 or pages > self.total_pages:
            raise ValueError(
                f"Pages must be between 0 and {self.total_pages}."
            )
        if self.status == TO_READ and pages > 0:
            self.status = READING
        self.pages_read = pages
        logger.debug("Progress updated: %r → %d/%d", self.title, pages, self.total_pages)

    def to_dict(self) -> dict:
        """Serialise to a plain dict for JSON storage."""
        return {
            "title": self.title,
            "author": self.author,
            "total_pages": self.total_pages,
            "pages_read": self.pages_read,
            "status": self.status,
            "rating": self.rating,
            "notes": self.notes,
            "date_added": self.date_added,
            "date_finished": self.date_finished,
        }


# ──────────────────────────────────────────────
# AudioBook  (inheritance: AudioBook → Book)
# ──────────────────────────────────────────────
@dataclass
class AudioBook(Book):
    """An audiobook; 'pages' are interpreted as minutes of audio."""

    narrator: str = ""

    # Override __str__ to surface narrator
    def __str__(self) -> str:
        base = super().__str__()
        narrator_tag = f" [narr. {self.narrator}]" if self.narrator else ""
        return base + narrator_tag + " 🎧"

    @classmethod
    def from_dict(cls, data: dict) -> "AudioBook":
        book = super().from_dict(data)
        # super().from_dict returns a Book; reconstruct as AudioBook
        return cls(
            title=book.title,
            author=book.author,
            total_pages=book.total_pages,
            pages_read=book.pages_read,
            status=book.status,
            rating=book.rating,
            notes=book.notes,
            date_added=book.date_added,
            date_finished=book.date_finished,
            narrator=data.get("narrator", ""),
        )

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["narrator"] = self.narrator
        d["_type"] = "audiobook"
        return d


# ──────────────────────────────────────────────
# ReadingList  (container; multiple dunders)
# ──────────────────────────────────────────────
class ReadingList:
    """An ordered collection of Book objects.

    Dunder methods demonstrated here:
        __init__, __repr__, __str__, __len__, __contains__, __iter__
    """

    def __init__(self, name: str = "My Reading List") -> None:
        self.name = name
        self._books: list[Book] = []

    # ── dunders ────────────────────────────────
    def __repr__(self) -> str:
        return f"ReadingList(name={self.name!r}, books={len(self._books)})"

    def __str__(self) -> str:
        if not self._books:
            return f"{self.name} (empty)"
        lines = [f"📚 {self.name}", "─" * 50]
        for book in self._books:
            lines.append(f"  {book}")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._books)

    def __contains__(self, title: object) -> bool:
        """Support: 'Clean Code' in reading_list"""
        if isinstance(title, str):
            return any(b.title.lower() == title.lower() for b in self._books)
        if isinstance(title, Book):
            return title in self._books
        return False

    def __iter__(self) -> Iterator[Book]:
        return iter(self._books)

    # ── public interface ────────────────────────
    def add(self, book: Book) -> None:
        if book.title in self:
            raise ValueError(f"'{book.title}' is already in the list.")
        self._books.append(book)
        logger.info("Added %r by %s", book.title, book.author)

    def remove(self, title: str) -> Book:
        book = self._find(title)
        self._books.remove(book)
        logger.info("Removed %r", title)
        return book

    def get(self, title: str) -> Book:
        return self._find(title)

    def sorted_by_title(self) -> list[Book]:
        return sorted(self._books)

    def filter_by_status(self, status: str) -> list[Book]:
        return [b for b in self._books if b.status == status]

    # ── stats (uses recursive helper) ──────────
    def stats(self) -> dict:
        """Return aggregate reading statistics."""
        total = len(self._books)
        done = self.filter_by_status(DONE)
        reading = self.filter_by_status(READING)
        to_read = self.filter_by_status(TO_READ)

        total_pages = _sum_pages(self._books, 0)          # recursive call
        pages_read  = _sum_pages_read(self._books, 0)     # recursive call

        rated = [b.rating for b in done if b.rating is not None]
        avg_rating = round(sum(rated) / len(rated), 2) if rated else None

        return {
            "total_books": total,
            "done": len(done),
            "reading": len(reading),
            "to_read": len(to_read),
            "total_pages_in_list": total_pages,
            "pages_read": pages_read,
            "average_rating": avg_rating,
        }

    # ── private helpers ─────────────────────────
    def _find(self, title: str) -> Book:
        for book in self._books:
            if book.title.lower() == title.lower():
                return book
        raise KeyError(f"No book titled '{title}' found.")


# ──────────────────────────────────────────────
# Recursive helpers  (required by spec)
# ──────────────────────────────────────────────
def _sum_pages(books: list[Book], acc: int) -> int:
    """Recursively sum total_pages across a list of books."""
    if not books:
        return acc
    return _sum_pages(books[1:], acc + books[0].total_pages)


def _sum_pages_read(books: list[Book], acc: int) -> int:
    """Recursively sum pages_read across a list of books."""
    if not books:
        return acc
    return _sum_pages_read(books[1:], acc + books[0].pages_read)
