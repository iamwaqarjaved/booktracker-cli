# Build a CLI Reading Tracker in Python — Step-by-Step Tutorial

> **What you'll build:** A fully working command-line app called `booktracker` that lets you manage your personal reading list, track progress page-by-page, record star ratings, and view reading statistics — all stored in a local JSON file with zero external dependencies.

```bash
$ booktracker add "Clean Code" "Robert C. Martin" 431
✅  Added: [TO-READ  ] Clean Code — Robert C. Martin (0.0%)

$ booktracker finish "Clean Code" --rating 4.5
🎉  Finished: [DONE    ] Clean Code — Robert C. Martin (100.0%  ★ 4.5)

$ booktracker stats
📈  Reading Statistics
──────────────────────────────
  Total books     : 3
  Done            : 1
  Pages read      : 431
  Avg rating      : 4.50 ★
```

**Skills you'll practice:** `@dataclass`, inheritance, `@property`, dunder methods (`__str__`, `__lt__`, `__hash__`, `__len__`, `__contains__`, `__iter__`), recursion, file I/O, `argparse`, and Python packaging.

**Prerequisites:** Python 3.10+, basic familiarity with classes and functions.  
**Time to complete:** ~3–4 hours working through all steps.  
**Finished repo:** [github.com/iamwaqarjaved/booktracker-cli](https://github.com/iamwaqarjaved/booktracker-cli)

---

## Table of Contents

1. [Project overview and architecture](#step-1-project-overview-and-architecture)
2. [Set up the project structure](#step-2-set-up-the-project-structure)
3. [Build the Book model with @dataclass](#step-3-build-the-book-model-with-dataclass)
4. [Add properties and business methods](#step-4-add-properties-and-business-methods)
5. [Implement dunder methods](#step-5-implement-dunder-methods)
6. [Extend with inheritance — AudioBook](#step-6-extend-with-inheritance--audiobook)
7. [Build the ReadingList container class](#step-7-build-the-readinglist-container-class)
8. [Add recursive helpers for statistics](#step-8-add-recursive-helpers-for-statistics)
9. [Build the Store — JSON persistence](#step-9-build-the-store--json-persistence)
10. [Build the CLI with argparse](#step-10-build-the-cli-with-argparse)
11. [Write the test suite with pytest](#step-11-write-the-test-suite-with-pytest)
12. [Package and install the project](#step-12-package-and-install-the-project)
13. [Run the full application](#step-13-run-the-full-application)
14. [Concepts recap](#step-14-concepts-recap)

---

## Step 1: Project Overview and Architecture

Before writing any code, understand how the pieces fit together.

### What we're building

`booktracker` is a CLI tool with eight subcommands:

| Command | What it does |
|---------|-------------|
| `booktracker add "Title" "Author" 300` | Add a new book |
| `booktracker start "Title"` | Mark as currently reading |
| `booktracker progress "Title" 150` | Update pages read |
| `booktracker finish "Title" --rating 4.5` | Mark as done |
| `booktracker remove "Title"` | Delete from list |
| `booktracker list --status done` | Show books (filterable) |
| `booktracker stats` | Aggregate reading statistics |
| `booktracker note "Title" "Text"` | Append a note |

### Architecture — how the modules connect

```
┌─────────────────────────────────────────────────────┐
│  Terminal input                                      │
│  $ booktracker finish "Clean Code" --rating 4.5     │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  cli.py                                              │
│  _build_parser() → argparse parses the command      │
│  _handle_finish(args, store) dispatches the work    │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
           ▼                      ▼
┌──────────────────┐   ┌──────────────────────────────┐
│  models.py       │   │  store.py                     │
│  Book            │   │  Store.load()  → ReadingList  │
│  AudioBook       │   │  Store.save()  → books.json   │
│  ReadingList     │   └──────────────────────────────┘
│  _sum_pages()    │
└──────────────────┘
```

**Key design principles used throughout:**
- `models.py` has no knowledge of the CLI or persistence — it is pure domain logic
- `store.py` knows about `models.py` but not `cli.py`
- `cli.py` orchestrates everything: it parses input, calls the store, calls business methods, and prints output
- Zero external runtime dependencies — runs on any Python 3.10+ install

---

## Step 2: Set Up the Project Structure

Create the directory layout first. Using a `src/` layout is a modern Python packaging best practice — it prevents accidental imports from the repo root and catches missing `__init__.py` files early.

```bash
mkdir booktracker-cli
cd booktracker-cli

# Create the package directory
mkdir -p src/booktracker
mkdir -p tests
mkdir -p docs

# Create all the files we'll fill in
touch src/booktracker/__init__.py
touch src/booktracker/models.py
touch src/booktracker/store.py
touch src/booktracker/cli.py
touch tests/__init__.py
touch tests/test_models.py
touch tests/test_cli.py
touch pyproject.toml
touch requirements.txt
touch README.md
```

Your structure should look like this:

```
booktracker-cli/
├── src/
│   └── booktracker/
│       ├── __init__.py
│       ├── models.py
│       ├── store.py
│       └── cli.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   └── test_cli.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Create pyproject.toml

This file tells Python how to build and install your package. Note `dependencies = []` — we're using stdlib only.

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "booktracker-cli"
version = "1.0.0"
description = "A command-line personal reading list manager"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
authors = [{ name = "Your Name", email = "you@example.com" }]
dependencies = []          # stdlib only — zero external runtime deps

[project.scripts]
booktracker = "booktracker.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-dir]
"" = "src"
```

The `[project.scripts]` entry is what makes `booktracker` available as a shell command after installation. It points to the `main()` function in `cli.py`.

### Create requirements.txt (dev dependencies only)

```
# requirements.txt
# Runtime: stdlib only — no external packages required.
# Dev / test dependencies:
pytest>=7.4
```

### Fill in __init__.py

```python
# src/booktracker/__init__.py
"""booktracker — personal reading list manager."""

__version__ = "1.0.0"
__all__ = ["Book", "ReadingList", "Store"]
```

---

## Step 3: Build the Book Model with @dataclass

The `Book` class is the heart of the application. We'll use `@dataclass` to eliminate `__init__` boilerplate while keeping all field declarations visible at the class level.

Open `src/booktracker/models.py` and start building:

```python
"""
models.py
---------
Domain model for BookTracker.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from typing import Iterator

logger = logging.getLogger(__name__)

# ── Status constants ────────────────────────────
TO_READ = "to-read"
READING = "reading"
DONE    = "done"
VALID_STATUSES = (TO_READ, READING, DONE)


# ── Book ────────────────────────────────────────
@dataclass
class Book:
    """Represents a single book in the reading list."""

    title: str
    author: str
    total_pages: int
    pages_read: int = 0
    status: str = TO_READ
    rating: float | None = None
    notes: str = ""
    date_added: str = field(
        default_factory=lambda: datetime.date.today().isoformat()
    )
    date_finished: str | None = None
```

**Why `@dataclass`?**  
Without it, you'd write:

```python
# Without @dataclass — 12 lines of boring boilerplate:
class Book:
    def __init__(self, title, author, total_pages, pages_read=0,
                 status="to-read", rating=None, notes="",
                 date_added=None, date_finished=None):
        self.title = title
        self.author = author
        self.total_pages = total_pages
        ...
```

`@dataclass` generates `__init__`, `__repr__`, and `__eq__` automatically from the field declarations.

**Why `field(default_factory=...)`?**  
Writing `date_added: str = datetime.date.today().isoformat()` would evaluate `today()` *once at class definition time* — every book would have the same date. The `default_factory` calls the function fresh each time a `Book` is created.

### Add the classmethod constructors

```python
    # ── @classmethod alternate constructors ─────
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
        """Shorthand constructor — useful in tests."""
        return cls(title=title, author=author, total_pages=pages)
```

`@classmethod` gives you multiple ways to create a `Book`. `from_dict` is used by the `Store` when loading from JSON; `quick` is a convenience constructor for tests.

### Add serialization

```python
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
```

---

## Step 4: Add Properties and Business Methods

Properties let us compute derived values and validate state transitions. Business methods encode the rules of what a `Book` can do.

Add these inside the `Book` class, below the field declarations:

```python
    # ── @property ───────────────────────────────
    @property
    def progress_pct(self) -> float:
        """Percentage of pages read (0–100)."""
        if self.total_pages <= 0:
            return 0.0
        return round(self.pages_read / self.total_pages * 100, 1)

    @property
    def is_finished(self) -> bool:
        return self.status == DONE

    # ── Business methods ─────────────────────────
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
            self.status = READING      # auto-start on first progress update
        self.pages_read = pages
        logger.debug("Progress: %r → %d/%d", self.title, pages, self.total_pages)
```

**Why raise `ValueError` instead of silently ignoring bad input?**  
The `cli.py` handlers catch `ValueError` and display a friendly `❌` error message. Raising at the model layer keeps business rules in one place — the `CLI` doesn't need to know that you can't finish a book twice.

**Why does `update_progress` auto-start reading?**  
It follows the principle of least surprise: if you record 50 pages read on a `to-read` book, you're obviously reading it. Auto-transitioning saves the user a separate `start` command.

---

## Step 5: Implement Dunder Methods

Dunder (double-underscore) methods integrate your class with Python's built-in operations. Add these to the `Book` class:

```python
    # ── dunder: __str__ ─────────────────────────
    def __str__(self) -> str:
        stars = f"  ★ {self.rating:.1f}" if self.rating is not None else ""
        return (
            f"[{self.status.upper():8}] {self.title} — {self.author} "
            f"({self.progress_pct}%{stars})"
        )

    # ── dunder: __lt__ (enables sorting) ────────
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Book):
            return NotImplemented
        return self.title.lower() < other.title.lower()

    # ── dunder: __hash__ ────────────────────────
    def __hash__(self) -> int:
        return hash((self.title.lower(), self.author.lower()))
```

**Why `__lt__` and not `__gt__`, `__le__`, `__ge__`?**  
Python's `sorted()` only requires `__lt__`. That's all you need to make `sorted(books)` work alphabetically by title.

**Why does `__hash__` exist?**  
`@dataclass` with `eq=True` (the default) automatically sets `__hash__ = None` — making `Book` unhashable. Since we want to be able to use books in sets and as dict keys, we define `__hash__` explicitly on `(title.lower(), author.lower())`. This must match the equality semantics: two books that compare equal must have the same hash.

> ⚠️ **Watch out:** if you add `__eq__` to any class manually, Python sets `__hash__ = None`. Always define `__hash__` explicitly if you also need your object in sets or dicts.

**Return `NotImplemented` (not `False`) from comparison methods.**  
When `other` isn't a `Book`, returning `NotImplemented` lets Python try the reflected operation on the other object. Returning `False` silently produces wrong results in some comparison scenarios.

---

## Step 6: Extend with Inheritance — AudioBook

`AudioBook` is a `Book` where "pages" means "minutes of audio" and there's an additional `narrator` field. This is a genuine `is-a` relationship — an audiobook *is* a book with extra metadata.

Add this class after `Book` in `models.py`:

```python
# ── AudioBook (inheritance: AudioBook → Book) ──
@dataclass
class AudioBook(Book):
    """An audiobook; 'pages' are interpreted as minutes of audio."""

    narrator: str = ""

    # Override __str__ to surface the narrator
    def __str__(self) -> str:
        base = super().__str__()          # reuse parent's formatted string
        narrator_tag = f" [narr. {self.narrator}]" if self.narrator else ""
        return base + narrator_tag + " 🎧"

    @classmethod
    def from_dict(cls, data: dict) -> "AudioBook":
        # super().from_dict() returns a Book; unpack it into AudioBook
        book = super().from_dict(data)
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
        d = super().to_dict()             # serialise shared fields
        d["narrator"] = self.narrator
        d["_type"] = "audiobook"          # type tag for Store to discriminate
        return d
```

**Key patterns to notice:**

`super().__str__()` calls the parent's method and extends it — instead of copy-pasting the formatting logic, `AudioBook.__str__` reuses `Book.__str__` and appends the narrator and 🎧 emoji.

`d["_type"] = "audiobook"` adds a discriminator field to the JSON. When `Store.load()` reads the file back, it checks `_type` to decide whether to call `Book.from_dict()` or `AudioBook.from_dict()`.

**Why not just put `narrator` on `Book`?**  
It would mean every regular `Book` carries a `narrator` field that is always empty, making the schema messier and the intent less clear. Inheritance lets `AudioBook` *add* to the contract without polluting the base class.

> 💡 **@dataclass inheritance gotcha:** A `@dataclass` subclass that adds a field *with a default* must ensure all parent fields with defaults come before it in the MRO. Since all of `Book`'s non-required fields have defaults and `narrator` also has a default (`""`), this works fine.

---

## Step 7: Build the ReadingList Container Class

`ReadingList` is a stateful container for `Book` objects. It's a plain class (not a `@dataclass`) because its behavior is container-first, not record-first.

Add this after `AudioBook` in `models.py`:

```python
# ── ReadingList (container; multiple dunders) ──
class ReadingList:
    """An ordered collection of Book objects."""

    def __init__(self, name: str = "My Reading List") -> None:
        self.name = name
        self._books: list[Book] = []

    # ── Dunders ─────────────────────────────────
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
        """Support: 'Clean Code' in reading_list  OR  book_obj in reading_list"""
        if isinstance(title, str):
            return any(b.title.lower() == title.lower() for b in self._books)
        if isinstance(title, Book):
            return title in self._books
        return False

    def __iter__(self) -> Iterator[Book]:
        return iter(self._books)

    # ── Public interface ─────────────────────────
    def add(self, book: Book) -> None:
        if book.title in self:          # uses __contains__
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
        return sorted(self._books)      # uses Book.__lt__

    def filter_by_status(self, status: str) -> list[Book]:
        return [b for b in self._books if b.status == status]

    def stats(self) -> dict:
        """Return aggregate reading statistics."""
        done    = self.filter_by_status(DONE)
        reading = self.filter_by_status(READING)
        to_read = self.filter_by_status(TO_READ)

        total_pages = _sum_pages(self._books, 0)        # recursive call
        pages_read  = _sum_pages_read(self._books, 0)   # recursive call

        rated = [b.rating for b in done if b.rating is not None]
        avg_rating = round(sum(rated) / len(rated), 2) if rated else None

        return {
            "total_books": len(self._books),
            "done": len(done),
            "reading": len(reading),
            "to_read": len(to_read),
            "total_pages_in_list": total_pages,
            "pages_read": pages_read,
            "average_rating": avg_rating,
        }

    # ── Private helpers ──────────────────────────
    def _find(self, title: str) -> Book:
        for book in self._books:
            if book.title.lower() == title.lower():
                return book
        raise KeyError(f"No book titled '{title}' found.")
```

**Notice how dunders enable clean code elsewhere:**
- `add()` writes `if book.title in self` — readable because `__contains__` exists
- `sorted_by_title()` writes `sorted(self._books)` — works because `Book.__lt__` exists
- `Store.save()` will write `for b in reading_list` — works because `__iter__` exists
- Tests write `assert len(rl) == 2` — works because `__len__` exists

The `__contains__` method accepts both `str` and `Book` arguments. This is intentional: `add()` checks by title string (`"Clean Code" in self`), while tests can also check with a `Book` object (`assert book_obj in rl`).

---

## Step 8: Add Recursive Helpers for Statistics

The spec requires at least one recursive function. Here's the key: recursion should reflect the structure of the *problem*, not be forced onto it. Summing a list of values is naturally recursive — the sum of a list is the first element plus the sum of the rest.

Add these module-level functions at the bottom of `models.py`:

```python
# ── Recursive helpers ────────────────────────────
def _sum_pages(books: list[Book], acc: int) -> int:
    """Recursively sum total_pages across a list of books.

    Uses an accumulator parameter (tail-recursive style):
      _sum_pages([b1, b2, b3], 0)
        → _sum_pages([b2, b3], 0 + b1.total_pages)
        → _sum_pages([b3],     b1 + b2)
        → _sum_pages([],       b1 + b2 + b3)
        → returns b1 + b2 + b3
    """
    if not books:           # base case: empty list
        return acc
    return _sum_pages(books[1:], acc + books[0].total_pages)


def _sum_pages_read(books: list[Book], acc: int) -> int:
    """Recursively sum pages_read across a list of books."""
    if not books:
        return acc
    return _sum_pages_read(books[1:], acc + books[0].pages_read)
```

**Anatomy of a recursive function:**

Every recursive function needs two things:
1. **A base case** that stops the recursion (`if not books: return acc`)
2. **A recursive case** that calls itself with a *smaller* input (`books[1:]` is one element shorter each call)

The **accumulator pattern** (`acc` parameter) builds up the result through the parameter rather than the return value stack. It's inspired by tail-recursive style from functional programming — even though CPython doesn't optimize tail calls, the pattern is worth learning.

> ⚠️ **Python's recursion limit:** CPython defaults to 1,000 stack frames. For a personal reading list, you'd need 990+ books to hit this — not a real concern. But it's why `sum(b.total_pages for b in books)` is the production choice, and the recursive version is the teaching choice.

---

## Step 9: Build the Store — JSON Persistence

The `Store` class handles all file I/O. It lives in `store.py` so that `models.py` stays completely independent of persistence concerns.

```python
# src/booktracker/store.py
"""
store.py
--------
JSON-backed persistence for ReadingList.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from booktracker.models import AudioBook, Book, ReadingList

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path.home() / ".booktracker" / "books.json"


class Store:
    """Loads and saves a ReadingList to a JSON file."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_PATH

    def load(self) -> ReadingList:
        """Read the JSON file and return a populated ReadingList."""
        rl = ReadingList()
        if not self.path.exists():
            logger.debug("Store not found at %s — starting fresh.", self.path)
            return rl

        try:
            raw = self.path.read_text(encoding="utf-8").strip()
            if not raw:
                return rl
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Corrupt store file at {self.path}: {exc}") from exc
        except PermissionError as exc:
            raise PermissionError(f"Cannot read {self.path}: {exc}") from exc

        for item in data.get("books", []):
            # Discriminate on _type to reconstruct the correct subclass
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
            raise PermissionError(f"Cannot write {self.path}: {exc}") from exc
        logger.info("Saved %d book(s) to %s", len(reading_list), self.path)
```

**What to notice:**

`self.path.parent.mkdir(parents=True, exist_ok=True)` creates `~/.booktracker/` on first run without crashing if it already exists.

`for b in reading_list` works in `save()` because `ReadingList.__iter__` exists.

`data.get("books", [])` means an empty or malformed file returns an empty list rather than a `KeyError` — defensive loading.

The `path` constructor parameter is the most important design decision here for testability: `Store(path=tmp_path / "books.json")` lets tests use a temp file instead of the real `~/.booktracker/books.json`. All 8 integration tests rely on this.

---

## Step 10: Build the CLI with argparse

The CLI is the largest file but the most mechanical. The pattern is: build a parser, write one handler function per subcommand, dispatch via a dictionary.

```python
# src/booktracker/cli.py
"""
cli.py
------
Command-line interface for BookTracker using argparse.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from booktracker.models import VALID_STATUSES, AudioBook, Book
from booktracker.store import Store

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
```

### Build the parser

```python
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="booktracker",
        description="📚 BookTracker — your personal reading list manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  booktracker add 'Clean Code' 'Robert C. Martin' 431\n"
            "  booktracker start 'Clean Code'\n"
            "  booktracker progress 'Clean Code' 200\n"
            "  booktracker finish 'Clean Code' --rating 4.5\n"
            "  booktracker list --status done\n"
            "  booktracker stats\n"
        ),
    )
    # Global flags available to all subcommands
    parser.add_argument("--store", metavar="FILE",
                        help="Path to JSON store (default: ~/.booktracker/books.json)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose (DEBUG) logging")

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True    # error if user runs `booktracker` with no subcommand

    # ── add ──
    p_add = sub.add_parser("add", help="Add a new book")
    p_add.add_argument("title",  help="Book title (quote if multi-word)")
    p_add.add_argument("author", help="Author name")
    p_add.add_argument("pages",  type=int, help="Total pages (or minutes for audiobooks)")
    p_add.add_argument("--audio",    action="store_true", help="Treat as audiobook")
    p_add.add_argument("--narrator", default="", help="Narrator name (audiobook only)")

    # ── start ──
    p_start = sub.add_parser("start", help="Mark a book as currently reading")
    p_start.add_argument("title", help="Book title")

    # ── progress ──
    p_prog = sub.add_parser("progress", help="Update pages read")
    p_prog.add_argument("title", help="Book title")
    p_prog.add_argument("pages", type=int, help="Pages read so far")

    # ── finish ──
    p_fin = sub.add_parser("finish", help="Mark a book as finished")
    p_fin.add_argument("title", help="Book title")
    p_fin.add_argument("--rating", type=float, metavar="0-5", help="Star rating (0.0–5.0)")

    # ── remove ──
    p_rem = sub.add_parser("remove", help="Remove a book from the list")
    p_rem.add_argument("title", help="Book title")

    # ── list ──
    p_list = sub.add_parser("list", help="List books")
    p_list.add_argument("--status", choices=VALID_STATUSES, default=None,
                        help="Filter by status")
    p_list.add_argument("--sort", action="store_true", help="Sort alphabetically")

    # ── stats ──
    sub.add_parser("stats", help="Show reading statistics")

    # ── note ──
    p_note = sub.add_parser("note", help="Add a note to a book")
    p_note.add_argument("title", help="Book title")
    p_note.add_argument("text",  help="Note text to append")

    return parser
```

### Write the command handlers

Each handler follows the same pattern: load → mutate → save → print result.

```python
def _handle_add(args, store: Store) -> int:
    rl = store.load()
    if args.audio:
        book = AudioBook(title=args.title, author=args.author,
                         total_pages=args.pages, narrator=args.narrator)
    else:
        book = Book.quick(args.title, args.author, args.pages)
    try:
        rl.add(book)
    except ValueError as exc:
        print(f"❌  {exc}", file=sys.stderr)
        return 1
    store.save(rl)
    print(f"✅  Added: {book}")
    return 0


def _handle_start(args, store: Store) -> int:
    rl = store.load()
    try:
        book = rl.get(args.title)
        book.start_reading()
    except (KeyError, ValueError) as exc:
        print(f"❌  {exc}", file=sys.stderr)
        return 1
    store.save(rl)
    print(f"📖  Started: {book}")
    return 0


def _handle_progress(args, store: Store) -> int:
    rl = store.load()
    try:
        book = rl.get(args.title)
        book.update_progress(args.pages)
    except (KeyError, ValueError) as exc:
        print(f"❌  {exc}", file=sys.stderr)
        return 1
    store.save(rl)
    print(f"📊  Progress: {book}")
    return 0


def _handle_finish(args, store: Store) -> int:
    rl = store.load()
    try:
        book = rl.get(args.title)
        book.finish(rating=args.rating)
    except (KeyError, ValueError) as exc:
        print(f"❌  {exc}", file=sys.stderr)
        return 1
    store.save(rl)
    print(f"🎉  Finished: {book}")
    return 0


def _handle_remove(args, store: Store) -> int:
    rl = store.load()
    try:
        book = rl.remove(args.title)
    except KeyError as exc:
        print(f"❌  {exc}", file=sys.stderr)
        return 1
    store.save(rl)
    print(f"🗑️   Removed: {book.title}")
    return 0


def _handle_list(args, store: Store) -> int:
    rl = store.load()
    if len(rl) == 0:
        print("Your reading list is empty. Add a book with: booktracker add")
        return 0

    books = rl.filter_by_status(args.status) if args.status else list(rl)
    if args.sort:
        books = sorted(books)     # uses Book.__lt__

    if not books:
        print(f"No books with status '{args.status}'.")
        return 0

    # Print a formatted table
    col = {"title": 32, "author": 22, "status": 10, "progress": 10, "rating": 6}
    header = (
        f"{'Title':<{col['title']}} {'Author':<{col['author']}} "
        f"{'Status':<{col['status']}} {'Progress':>{col['progress']}} "
        f"{'Rating':>{col['rating']}}"
    )
    sep = "─" * len(header)
    print(f"\n📚  {len(books)} book(s)\n{sep}\n{header}\n{sep}")
    for b in books:
        rating_str = f"{b.rating:.1f} ★" if b.rating is not None else "—"
        title_d  = b.title[:col["title"]  - 1] if len(b.title)  > col["title"]  - 1 else b.title
        author_d = b.author[:col["author"] - 1] if len(b.author) > col["author"] - 1 else b.author
        print(
            f"{title_d:<{col['title']}} {author_d:<{col['author']}} "
            f"{b.status:<{col['status']}} {b.progress_pct:>8.1f}%  "
            f"{rating_str:>{col['rating']}}"
        )
    print(sep)
    return 0


def _handle_stats(args, store: Store) -> int:
    rl = store.load()
    s = rl.stats()
    print("\n📈  Reading Statistics")
    print("─" * 30)
    print(f"  Total books     : {s['total_books']}")
    print(f"  Done            : {s['done']}")
    print(f"  Reading now     : {s['reading']}")
    print(f"  To read         : {s['to_read']}")
    print(f"  Pages in list   : {s['total_pages_in_list']:,}")
    print(f"  Pages read      : {s['pages_read']:,}")
    avg = f"{s['average_rating']:.2f} ★" if s["average_rating"] is not None else "n/a"
    print(f"  Avg rating      : {avg}")
    print("─" * 30)
    return 0


def _handle_note(args, store: Store) -> int:
    rl = store.load()
    try:
        book = rl.get(args.title)
    except KeyError as exc:
        print(f"❌  {exc}", file=sys.stderr)
        return 1
    separator = "\n" if book.notes else ""
    book.notes += f"{separator}{args.text}"
    store.save(rl)
    print(f"📝  Note saved for '{book.title}'.")
    return 0
```

### Write the entry point

The `_HANDLERS` dictionary dispatch is the key pattern: adding a ninth command requires one line here and one new function, with zero changes to `main()`.

```python
_HANDLERS = {
    "add":      _handle_add,
    "start":    _handle_start,
    "progress": _handle_progress,
    "finish":   _handle_finish,
    "remove":   _handle_remove,
    "list":     _handle_list,
    "stats":    _handle_stats,
    "note":     _handle_note,
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    store = Store(path=args.store if args.store else None)

    handler = _HANDLERS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args, store)
    except Exception as exc:
        logger.exception("Unexpected error")
        print(f"💥  Unexpected error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

**Why does `main()` accept `argv`?**  
When called from the shell, `argv=None` makes `argparse` read `sys.argv`. In tests, passing `["--store", "/tmp/test.json", "add", "Dune", "Herbert", "412"]` overrides `sys.argv` entirely — no mocking required.

---

## Step 11: Write the Test Suite with pytest

Good tests validate behavior, not implementation. Structure them around what the class *does*, not how it's built.

### Unit tests for models

```python
# tests/test_models.py
"""Tests for models.py"""
import pytest
from booktracker.models import (
    AudioBook, Book, ReadingList,
    TO_READ, READING, DONE,
    _sum_pages, _sum_pages_read,
)


class TestBook:
    def test_default_status(self):
        b = Book("Title", "Author", 100)
        assert b.status == TO_READ

    def test_progress_pct(self):
        b = Book("T", "A", 200, pages_read=50)
        assert b.progress_pct == 25.0

    def test_start_reading(self):
        b = Book.quick("T", "A", 100)
        b.start_reading()
        assert b.status == READING

    def test_start_reading_already_reading_raises(self):
        b = Book.quick("T", "A", 100)
        b.start_reading()
        with pytest.raises(ValueError):
            b.start_reading()        # can't start twice

    def test_finish(self):
        b = Book.quick("T", "A", 100)
        b.start_reading()
        b.finish(rating=4.0)
        assert b.status == DONE
        assert b.rating == 4.0
        assert b.pages_read == 100   # finish() sets pages_read to total

    def test_finish_invalid_rating(self):
        b = Book.quick("T", "A", 100)
        b.start_reading()
        with pytest.raises(ValueError):
            b.finish(rating=6.0)     # rating must be 0–5

    def test_update_progress_auto_starts(self):
        b = Book.quick("T", "A", 100)
        b.update_progress(10)
        assert b.status == READING   # auto-started from TO_READ

    def test_lt_sorting(self):
        a = Book.quick("Zebra", "Author", 100)
        b = Book.quick("Apple", "Author", 100)
        assert b < a                 # "Apple" < "Zebra" alphabetically

    def test_hash_uniqueness(self):
        b1 = Book.quick("Title", "Author", 100)
        b2 = Book.quick("Title", "Author", 200)  # different pages
        assert hash(b1) == hash(b2)  # same title+author → same hash

    def test_round_trip_dict(self):
        b = Book.quick("Round Trip", "Tester", 50)
        assert Book.from_dict(b.to_dict()).title == "Round Trip"


class TestAudioBook:
    def test_str_contains_headphones(self):
        ab = AudioBook("Dune", "Herbert", 600, narrator="Tim")
        assert "🎧" in str(ab)

    def test_to_dict_has_type_tag(self):
        ab = AudioBook("Dune", "Herbert", 600)
        assert ab.to_dict()["_type"] == "audiobook"


class TestReadingList:
    def _make_list(self):
        rl = ReadingList()
        rl.add(Book.quick("A", "Auth1", 100))
        rl.add(Book.quick("B", "Auth2", 200))
        return rl

    def test_len(self):
        assert len(self._make_list()) == 2

    def test_contains_by_string(self):
        assert "A" in self._make_list()

    def test_iter(self):
        titles = [b.title for b in self._make_list()]
        assert titles == ["A", "B"]

    def test_duplicate_raises(self):
        rl = ReadingList()
        rl.add(Book.quick("X", "Y", 10))
        with pytest.raises(ValueError):
            rl.add(Book.quick("X", "Z", 20))

    def test_remove(self):
        rl = self._make_list()
        rl.remove("A")
        assert len(rl) == 1

    def test_stats_total_pages(self):
        s = self._make_list().stats()
        assert s["total_pages_in_list"] == 300  # 100 + 200


# ── Recursive helpers ──────────────────────────
def test_recursive_sum_empty():
    assert _sum_pages([], 0) == 0

def test_recursive_sum_pages():
    books = [Book.quick("A", "X", 10), Book.quick("B", "Y", 20)]
    assert _sum_pages(books, 0) == 30

def test_recursive_sum_pages_read():
    b1 = Book.quick("A", "X", 100); b1.pages_read = 40
    b2 = Book.quick("B", "Y", 100); b2.pages_read = 60
    assert _sum_pages_read([b1, b2], 0) == 100
```

### Integration tests for the CLI

These tests call `main()` directly with a temp file — no mocking, no subprocess, just real end-to-end behavior:

```python
# tests/test_cli.py
"""Integration tests for the CLI."""
import json
from pathlib import Path

import pytest
from booktracker.cli import main


@pytest.fixture
def store_file(tmp_path):
    """Each test gets its own fresh JSON file in a temp directory."""
    return str(tmp_path / "books.json")


def run(*args, store):
    """Helper to call main() with a synthetic argv."""
    return main(["--store", store, *args])


class TestCLI:
    def test_add_book(self, store_file):
        rc = run("add", "Clean Code", "Robert C. Martin", "431", store=store_file)
        assert rc == 0
        data = json.loads(Path(store_file).read_text())
        assert data["books"][0]["title"] == "Clean Code"

    def test_duplicate_add_fails(self, store_file):
        run("add", "Dupe", "Author", "100", store=store_file)
        rc = run("add", "Dupe", "Author", "100", store=store_file)
        assert rc == 1              # second add returns exit code 1

    def test_start_and_progress(self, store_file):
        run("add", "Pragmatic", "Hunt", "352", store=store_file)
        run("start", "Pragmatic", store=store_file)
        rc = run("progress", "Pragmatic", "100", store=store_file)
        assert rc == 0

    def test_finish_with_rating(self, store_file):
        run("add", "SICP", "Abelson", "657", store=store_file)
        run("start", "SICP", store=store_file)
        rc = run("finish", "SICP", "--rating", "5.0", store=store_file)
        assert rc == 0

    def test_list(self, store_file):
        run("add", "Book1", "Auth", "100", store=store_file)
        assert run("list", store=store_file) == 0

    def test_stats(self, store_file):
        assert run("stats", store=store_file) == 0

    def test_note(self, store_file):
        run("add", "NoteBook", "Author", "50", store=store_file)
        run("note", "NoteBook", "Great opening chapter!", store=store_file)
        data = json.loads(Path(store_file).read_text())
        assert "Great opening chapter!" in data["books"][0]["notes"]

    def test_remove(self, store_file):
        run("add", "ToRemove", "X", "10", store=store_file)
        rc = run("remove", "ToRemove", store=store_file)
        assert rc == 0
```

**Run the tests:**

```bash
pip install pytest          # one-time dev setup
python -m pytest tests/ -v
```

Expected output:
```
tests/test_models.py::TestBook::test_default_status PASSED
tests/test_models.py::TestBook::test_progress_pct PASSED
...
tests/test_cli.py::TestCLI::test_add_book PASSED
...
========================= 29 passed in 0.06s =========================
```

---

## Step 12: Package and Install the Project

```bash
# From the repo root:
pip install -e .
```

The `-e` flag installs in "editable" mode — changes to your source files take effect immediately without reinstalling. After this, `booktracker` is available as a shell command.

**What does `pip install -e .` actually do?**  
It reads `pyproject.toml`, finds the package under `src/` as configured, and registers `booktracker.cli:main` as the `booktracker` shell script. The `src/` layout ensures the installed version is what gets imported, not whatever happens to be in your current directory.

---

## Step 13: Run the Full Application

Try the complete workflow:

```bash
# Add books
booktracker add "Clean Code" "Robert C. Martin" 431
booktracker add "The Pragmatic Programmer" "Hunt & Thomas" 352
booktracker add "Dune" "Frank Herbert" 412 --audio --narrator "Simon Vance"

# Start reading
booktracker start "Clean Code"

# Update progress
booktracker progress "Clean Code" 200

# Add a note
booktracker note "Clean Code" "Functions should do one thing — love this rule."

# Finish with rating
booktracker finish "Clean Code" --rating 4.5

# View your list
booktracker list
booktracker list --status done
booktracker list --sort

# Stats
booktracker stats

# Inspect the raw JSON (it's just a file)
cat ~/.booktracker/books.json
```

The raw JSON file looks like:

```json
{
  "books": [
    {
      "title": "Clean Code",
      "author": "Robert C. Martin",
      "total_pages": 431,
      "pages_read": 431,
      "status": "done",
      "rating": 4.5,
      "notes": "Functions should do one thing — love this rule.",
      "date_added": "2026-06-27",
      "date_finished": "2026-06-27"
    }
  ]
}
```

---

## Step 14: Concepts Recap

Here's every concept from Weeks 1–8 and exactly where it appears in this project:

| Concept | Where it lives | What it does |
|---------|---------------|-------------|
| Variables, types, f-strings | `models.py` fields, `cli.py` output | `rating: float \| None`, `f"[{status.upper():8}]"` |
| Control flow, loops | `cli.py` handlers, `store.py` | `if/else` in handlers, `for item in data` in load |
| Functions, scope | `_sum_pages`, `_sum_pages_read` | Module-level recursive helpers |
| Lists, dicts, comprehensions | `ReadingList._books`, `to_dict()` | `[b for b in self._books if b.status == status]` |
| File I/O, error handling, logging | `store.py` | `json.load/dump`, `try/except`, `logging.getLogger` |
| Classes, OOP basics | `Book`, `ReadingList` | Encapsulation, instance methods, `@property` |
| Inheritance, `@dataclass`, `@classmethod`, `@property` | `AudioBook`, `Book.from_dict`, `Book.progress_pct` | Subclassing, alternate constructors, computed attributes |
| Dunder methods (9 total) | `Book`, `ReadingList` | `__str__`, `__lt__`, `__hash__`, `__len__`, `__contains__`, `__iter__` |

### Dunder inventory

| Dunder | Class | How it's used |
|--------|-------|--------------|
| `__init__` | `Book` (via @dataclass) | `Book("Dune", "Herbert", 412)` |
| `__repr__` | `Book`, `ReadingList` | REPL and logging output |
| `__str__` | `Book`, `AudioBook`, `ReadingList` | `print(book)` in CLI handlers |
| `__eq__` | `Book` (via @dataclass) | Duplicate detection in `ReadingList.add()` |
| `__lt__` | `Book` | `sorted(books)` alphabetically by title |
| `__hash__` | `Book` | Required after defining `__eq__` |
| `__len__` | `ReadingList` | `len(rl)` in handlers and tests |
| `__contains__` | `ReadingList` | `"Clean Code" in reading_list` |
| `__iter__` | `ReadingList` | `for book in reading_list` in save() |

### Extension ideas

Once you're comfortable with the codebase, try these additions:

- **Genres and filtering** — add a `genre` field to `Book` and a `list --genre` flag to `cli.py`
- **Export to CSV** — add a `Store.export_csv()` method using the `csv` stdlib module
- **Reading goals** — track a yearly page goal and show progress in `stats`
- **Atomic writes** — improve `Store.save()` to use `tempfile.mkstemp` + `os.replace()` for crash safety
- **Shell completions** — add `argcomplete` to generate tab completions for book titles

---

## Where to Go From Here

- **Browse the finished code:** [github.com/iamwaqarjaved/booktracker-cli](https://github.com/iamwaqarjaved/booktracker-cli)
- **See the architecture decisions:** `docs/ADL.md` in the repo documents every design decision and the alternatives considered
- **Watch the demo:** [youtube.com/watch?v=vcex6zLIHoI](https://www.youtube.com/watch?v=vcex6zLIHoI)

---

*Tutorial by Waqar Javed · [github.com/iamwaqarjaved](https://github.com/iamwaqarjaved)*
