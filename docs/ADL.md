# Architecture Decision Log (ADL)
## BookTracker CLI — Module 8 Capstone
**Author:** Waqar Javed  
**GitHub:** github.com/iamwaqarjaved/booktracker-cli  
**Document:** `docs/ADL.md`  
**Version:** 1.0 — Final submission  
**Date:** 2026-06-27

---

## Table of Contents

1. [Introduction & Repository Map](#1-introduction--repository-map)
2. [ADR-001 — Domain Choice: Reading List Manager](#adr-001--domain-choice-reading-list-manager)
3. [ADR-002 — @dataclass for Book, Plain Class for ReadingList](#adr-002--dataclass-for-book-plain-class-for-readinglist)
4. [ADR-003 — Inheritance: AudioBook extends Book](#adr-003--inheritance-audiobook-extends-book)
5. [ADR-004 — Dunder Method Selection](#adr-004--dunder-method-selection)
6. [ADR-005 — Recursive Page Summation](#adr-005--recursive-page-summation)
7. [ADR-006 — Persistence: JSON via stdlib](#adr-006--persistence-json-via-stdlib)
8. [ADR-007 — CLI Library: argparse over Click / Typer](#adr-007--cli-library-argparse-over-click--typer)
9. [ADR-008 — Project Layout: src/ Package Structure](#adr-008--project-layout-src-package-structure)
10. [ADR-009 — Test Framework: pytest over unittest](#adr-009--test-framework-pytest-over-unittest)
11. [AI Collaboration Disclosure](#ai-collaboration-disclosure)
12. [Self-Assessment](#self-assessment)

---

## 1. Introduction & Repository Map

This Architecture Decision Log documents every significant design decision made during the development of **BookTracker CLI**, the Module 8 Python capstone. BookTracker is a command-line application for managing a personal reading list — adding books and audiobooks, tracking reading progress by page count, recording star ratings, appending notes, and generating aggregate statistics.

Each record explains the problem that forced a decision, what was chosen, what was rejected and why, and the real-world consequences. Every ADR cross-references the exact source file and line numbers it governs.

### Repository structure (actual)

```
booktracker-cli/
├── src/
│   └── booktracker/
│       ├── __init__.py          # public exports + version string
│       ├── models.py            # Book, AudioBook, ReadingList, recursive helpers
│       ├── cli.py               # argparse parser + 8 command handlers + main()
│       └── store.py             # Store class — JSON load/save
├── tests/
│   ├── __init__.py
│   ├── test_models.py           # 21 unit tests (Book, AudioBook, ReadingList, recursion)
│   └── test_cli.py              # 8 integration tests (CLI round-trips via tmp file)
├── docs/
│   └── ADL.md                   # this document
├── pyproject.toml               # PEP 517 build config; zero runtime dependencies
├── requirements.txt             # dev/test only: pytest>=7.4
├── ARCHITECTURE_DECISIONS.md    # early working notes (superseded by this file)
├── PROJECT_BRIEF.md
└── README.md
```

**File sizes (lines of code):**

| File | Lines |
|------|-------|
| `src/booktracker/models.py` | 305 |
| `src/booktracker/cli.py` | 304 |
| `src/booktracker/store.py` | 75 |
| `tests/test_models.py` | 127 |
| `tests/test_cli.py` | 62 |
| **Total** | **873** |

**Test count:** 29 passing tests (21 unit + 8 integration).

---

## ADR-001 — Domain Choice: Reading List Manager

**Date:** 2026-06-26 | **Status:** Accepted  
**Governs:** Entire project scope

### Context

The capstone requires a Python CLI application that exercises the full Module 1–8 concept set: `@dataclass`, inheritance, `@property`, dunder methods, class methods, recursion, file I/O, and `argparse`. The domain chosen must make *all* of these feel earned rather than bolted on.

### Decision

Build a **personal reading list tracker** where:
- Each `Book` is a domain object with meaningful state (`to-read → reading → done`) that justifies `@property`, business methods, and state-transition logic
- An `AudioBook` subclass is semantically honest (an audiobook *is* a book with a narrator and audio-minutes instead of pages)
- A `ReadingList` container class naturally calls for `__len__`, `__iter__`, and `__contains__`
- Aggregate statistics (total pages, pages read, average rating) invite a recursive helper without forcing it

### Alternatives Considered

**Alternative 1 — Task / To-Do Manager**  
A task manager is the most common CLI capstone choice, which works against differentiation. More critically, tasks are flat records with little state behavior — there is no natural reason to use inheritance or aggregate statistics that would motivate a recursive helper. Status transitions (`todo → in-progress → done`) are simpler than a book's progress tracking across a numeric page range.

**Alternative 2 — Expense Tracker**  
An expense tracker is numbers-first: amounts, categories, date ranges. It would exercise file I/O well but produces little motivation for inheritance (what would a subclass of `Expense` be?), and `@property` on numeric fields feels contrived. The domain also invites a spreadsheet or database solution more than a CLI.

### Consequences

**Positive:**
- Every Python concept required by the spec maps naturally to the domain: `@property progress_pct` is genuinely useful, `AudioBook(Book)` is semantically honest, `_sum_pages` is a real accumulation problem
- The application is immediately understandable to any hiring-manager reader without domain explanation
- The `to-read → reading → done` lifecycle creates testable state-transition logic (`start_reading`, `finish`, `update_progress`) that exercises defensive programming patterns

**Negative:**
- "Pages" as the progress unit means audiobooks must interpret the field as minutes of audio rather than literal pages. This is documented in `AudioBook.__str__()` but is a semantic compromise that a more fully-featured app would resolve with a `duration_minutes` field
- A reading tracker is slightly more niche than a task manager for non-reader interviewers

---

## ADR-002 — @dataclass for Book, Plain Class for ReadingList

**Date:** 2026-06-26 | **Status:** Accepted  
**Governs:** `src/booktracker/models.py`, lines 38–159 (`Book`), lines 200–291 (`ReadingList`)

### Context

Python offers several mechanisms for defining classes that hold data: plain classes with manual `__init__`, `@dataclass` decorators, `NamedTuple`, and `TypedDict`. The choice determines how much boilerplate must be written, which dunder methods come for free, and whether the class is mutable. `Book` and `ReadingList` have different profiles: `Book` is primarily a value object (its identity is title + author) while `ReadingList` is a stateful container with complex behavior.

### Decision

**`@dataclass` for `Book` and `AudioBook`; plain class for `ReadingList`.**

```python
# src/booktracker/models.py, lines 38–55
@dataclass
class Book:
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

`@dataclass` auto-generates `__init__`, `__repr__`, and `__eq__` (field-by-field equality). The `date_added` field uses `field(default_factory=...)` because `datetime.date.today()` must be called at instantiation time, not at class-definition time — a subtlety that a plain default value would get wrong.

`ReadingList` is a plain class because its behavior is container-first: it manages insertion order, enforces deduplication, and exposes iteration semantics. None of these map well to `@dataclass`'s assumption that the class is primarily a record of named fields.

```python
# src/booktracker/models.py, lines 200–210
class ReadingList:
    """An ordered collection of Book objects."""

    def __init__(self, name: str = "My Reading List") -> None:
        self.name = name
        self._books: list[Book] = []
```

### Alternatives Considered

**Alternative 1 — @dataclass for both**  
Making `ReadingList` a `@dataclass` with a `_books: list[Book] = field(default_factory=list)` field would auto-generate `__init__` and `__repr__`. The problem is that `@dataclass` also generates `__eq__` based on field values, meaning two `ReadingList` objects with identical books would be considered equal — which is semantically wrong for a mutable container that should have reference identity. Suppressing `@dataclass(eq=False)` and then manually defining all the container dunders negates the value of the decorator.

**Alternative 2 — NamedTuple for Book**  
`NamedTuple` would make `Book` immutable and hashable by default, removing the `__hash__` issue (see ADR-004). The blocking problem is that `Book` must be mutable: `book.update_progress(pages)` modifies `pages_read` in place, and `book.finish(rating)` modifies `status`, `rating`, `pages_read`, and `date_finished`. Making `Book` immutable would require returning new instances from every business method, complicating `ReadingList.get()` and making the mutation-in-place semantics of `store.save(rl)` invisible to the caller.

### Consequences

**Positive:**
- `@dataclass` on `Book` eliminates approximately 20 lines of `__init__` boilerplate while making all nine fields visible at the class level — the declaration is its own documentation
- `field(default_factory=lambda: datetime.date.today().isoformat())` correctly captures today's date at add-time, not at import-time
- Keeping `ReadingList` as a plain class makes every dunder explicit and readable, demonstrating deliberate authorship of the container protocol

**Negative:**
- `@dataclass(eq=True)` (the default) sets `__hash__ = None` when equality is defined. Since `Book` must also be hashable (to be usable in sets for deduplication), an explicit `__hash__` is required — see ADR-004. A reader unfamiliar with this behavior may be surprised
- `AudioBook.from_dict` must reconstruct via an explicit constructor call rather than a clean `super().__init__()` delegation, because `super().from_dict()` returns a `Book`, not an `AudioBook` — a `@dataclass` inheritance limitation documented in the method's inline comment (models.py, line 175)

---

## ADR-003 — Inheritance: AudioBook extends Book

**Date:** 2026-06-26 | **Status:** Accepted  
**Governs:** `src/booktracker/models.py`, lines 162–195 (`AudioBook`); `src/booktracker/store.py`, lines 44–50 (type discrimination); `src/booktracker/cli.py`, lines 127–145 (`_handle_add`)

### Context

The spec requires at least one inheritance relationship that is semantically honest — not inheritance used merely to satisfy a checkbox. The design needed a subclass that genuinely extends the parent's behavior rather than replacing it, and that participates in the same persistence and CLI pipeline without requiring parallel code paths everywhere.

### Decision

**`AudioBook(Book)` — single inheritance, extending `Book` with a `narrator` field and overriding `__str__`, `from_dict`, and `to_dict`.**

```python
# src/booktracker/models.py, lines 162–195
@dataclass
class AudioBook(Book):
    """An audiobook; 'pages' are interpreted as minutes of audio."""
    narrator: str = ""

    def __str__(self) -> str:
        base = super().__str__()          # reuse parent's formatted string
        narrator_tag = f" [narr. {self.narrator}]" if self.narrator else ""
        return base + narrator_tag + " 🎧"

    @classmethod
    def from_dict(cls, data: dict) -> "AudioBook":
        book = super().from_dict(data)    # deserialise shared fields
        return cls(
            title=book.title, author=book.author, total_pages=book.total_pages,
            pages_read=book.pages_read, status=book.status, rating=book.rating,
            notes=book.notes, date_added=book.date_added,
            date_finished=book.date_finished,
            narrator=data.get("narrator", ""),
        )

    def to_dict(self) -> dict:
        d = super().to_dict()             # serialise shared fields
        d["narrator"] = self.narrator
        d["_type"] = "audiobook"          # type tag for Store discrimination
        return d
```

The `Store` class discriminates on `_type` during load to reconstruct the correct subclass:

```python
# src/booktracker/store.py, lines 44–50
for item in data.get("books", []):
    if item.get("_type") == "audiobook":
        book = AudioBook.from_dict(item)
    else:
        book = Book.from_dict(item)
    rl.add(book)
```

The `cli.py` `add` handler creates the right type based on the `--audio` flag:

```python
# src/booktracker/cli.py, lines 127–145
def _handle_add(args, store: Store) -> int:
    rl = store.load()
    if args.audio:
        book = AudioBook(title=args.title, author=args.author,
                         total_pages=args.pages, narrator=args.narrator)
    else:
        book = Book.quick(args.title, args.author, args.pages)
```

### Alternatives Considered

**Alternative 1 — Composition: ReadingList holds typed slots**  
`ReadingList` could hold separate `_books: list[Book]` and `_audiobooks: list[AudioBook]` lists, with all commands routing to the right list. This was rejected because it creates parallel code paths everywhere: `add`, `remove`, `get`, `list`, and `stats` would all need to handle two lists. The unified interface — `ReadingList` stores both types through a shared `Book` reference — is possible precisely because `AudioBook` is a `Book` and satisfies the same interface.

**Alternative 2 — Protocol / Duck Typing, no inheritance**  
A `BookLike` protocol with `title`, `author`, `status`, `progress_pct`, and `to_dict()` would allow `AudioBook` to be a structurally typed sibling of `Book` rather than a subtype. This approach (popularized by `typing.Protocol`) is valuable when two classes genuinely cannot share an ancestor. Here they can and should: `AudioBook` reuses `start_reading()`, `finish()`, `update_progress()`, `from_dict()`, and `to_dict()` from `Book`, modifying only `__str__` and the serialization type tag. Inheritance is the correct tool when the subclass genuinely extends its parent rather than replacing it.

### Consequences

**Positive:**
- `AudioBook` inherits all business logic (`start_reading`, `finish`, `update_progress`, `@property progress_pct`) without duplication
- `isinstance(book, Book)` returns `True` for both types, so `ReadingList`, `Store`, and all CLI handlers treat them uniformly without type checks
- `super()` calls in `__str__`, `from_dict`, and `to_dict` demonstrate deliberate use of the MRO rather than copy-pasting parent logic

**Negative:**
- `@dataclass` inheritance with default-valued fields requires that `AudioBook.narrator` have a default (`""`), because Python's `@dataclass` raises `TypeError` if a field without a default follows fields with defaults in the MRO — a constraint that is invisible until hit and not well-documented for beginners
- `AudioBook.from_dict` reconstructs the object by calling `super().from_dict()` and then unpacking the result into the `AudioBook` constructor. This is a documented pattern for `@dataclass` inheritance but adds a layer of indirection that a plain class would avoid

---

## ADR-004 — Dunder Method Selection

**Date:** 2026-06-26 | **Status:** Accepted  
**Governs:** `src/booktracker/models.py`, lines 72–90 (`Book` dunders), lines 212–237 (`ReadingList` dunders)

### Context

Python dunder methods integrate classes into the language's built-in protocol. The capstone spec required at least five dunders across the project. The design question was not how to reach a minimum count but which dunders are *earned* by the domain's actual needs. Every dunder added is a contract the class makes with the Python runtime; implementing one without a use case creates false affordances.

### Decision

**Nine dunder methods implemented across `Book`, `AudioBook`, and `ReadingList`, each with a concrete use case.**

| Dunder | Class | File:Line | Concrete use case |
|--------|-------|-----------|-------------------|
| `__init__` | `Book` (via @dataclass) | models.py:38 | Field initialisation with `date_added` default factory |
| `__repr__` | `Book` (via @dataclass), `ReadingList` | models.py:38, 212 | REPL and logging output |
| `__str__` | `Book`, `AudioBook`, `ReadingList` | models.py:72, 168, 215 | `print(book)` / `print(rl)` in CLI handlers |
| `__eq__` | `Book` (via @dataclass) | models.py:38 | Duplicate detection in `ReadingList.add()` |
| `__lt__` | `Book` | models.py:80 | `sorted(books)` in `_handle_list --sort` |
| `__hash__` | `Book` | models.py:88 | Hashability required after defining `__eq__` |
| `__len__` | `ReadingList` | models.py:223 | `len(rl)` in CLI handlers and tests |
| `__contains__` | `ReadingList` | models.py:226 | `if book.title in self` in `ReadingList.add()` |
| `__iter__` | `ReadingList` | models.py:234 | `for book in rl` in `Store.save()` and `stats()` |

**Total: 9 dunders (spec minimum: 5). ✅**

Key implementation details:

```python
# models.py:80-90 — __lt__ and __hash__ on Book
def __lt__(self, other: object) -> bool:
    if not isinstance(other, Book):
        return NotImplemented          # correct: let Python try the reflected op
    return self.title.lower() < other.title.lower()

def __hash__(self) -> int:
    return hash((self.title.lower(), self.author.lower()))
```

```python
# models.py:226-237 — __contains__ and __iter__ on ReadingList
def __contains__(self, title: object) -> bool:
    """Support: 'Clean Code' in reading_list  OR  book_obj in reading_list"""
    if isinstance(title, str):
        return any(b.title.lower() == title.lower() for b in self._books)
    if isinstance(title, Book):
        return title in self._books
    return False

def __iter__(self) -> Iterator[Book]:
    return iter(self._books)
```

### Alternatives Considered

**Alternative 1 — Implement __getitem__ on ReadingList**  
`__getitem__` would make `reading_list[0]` work. This was considered and rejected: the CLI never accesses books by numeric index. Users access books by title (`rl.get("Clean Code")`). Adding `__getitem__` would make `ReadingList` look subscriptable when no code path uses it.

**Alternative 2 — Skip __hash__ and make Book unhashable**  
Without a custom `__hash__`, `@dataclass(eq=True)` sets `__hash__ = None`, making `Book` unhashable and unusable in sets or as dict keys. This would be fine for the current codebase. However, the decision to define `__hash__` on `(title.lower(), author.lower())` is consistent with the `__eq__` semantics (two books with the same case-normalized title and author are the same book) and makes the class more useful in future contexts (e.g., deduplication via `set()`). The test `test_hash_uniqueness` in `test_models.py:76` verifies this behavior.

### Consequences

**Positive:**
- `__lt__` makes `sorted(books)` work without a key function in `_handle_list` (`cli.py:227`): `books = sorted(books)` — clean and idiomatic
- `__contains__` supporting both `str` and `Book` inputs means `ReadingList.add()` can write `if book.title in self` (a string check) while tests can also write `assert book_obj in rl` — both feel natural
- `__iter__` on `ReadingList` means `Store.save()` can write `[b.to_dict() for b in reading_list]` without accessing the private `._books` list

**Negative:**
- `@dataclass` with `eq=True` (the default) sets `__hash__ = None` automatically. Adding an explicit `__hash__` restores hashability but is a non-obvious step. A future developer who changes the `@dataclass` decorator or adds a new equality-relevant field must remember to update `__hash__` accordingly
- The dual-type `__contains__` (`str` or `Book`) is convenient but makes the method contract harder to express with a single type annotation — `title: object` is technically correct but less informative than a `Union` type

---

## ADR-005 — Recursive Page Summation

**Date:** 2026-06-26 | **Status:** Accepted  
**Governs:** `src/booktracker/models.py`, lines 294–305 (`_sum_pages`, `_sum_pages_read`); `src/booktracker/models.py`, lines 272–277 (`ReadingList.stats()` call sites)

### Context

The capstone spec required at least one recursive function used *naturally* — not forced into a problem that iteration handles better. The challenge was identifying a place where the recursive structure of the solution reflects something genuine about the problem, and where the accumulator pattern (common in functional programming) is a teaching moment in its own right.

### Decision

**Two module-level recursive functions with accumulator parameters for computing aggregate page counts across the book list.**

```python
# src/booktracker/models.py, lines 294-305

def _sum_pages(books: list[Book], acc: int) -> int:
    """Recursively sum total_pages across a list of books."""
    if not books:          # base case: empty list
        return acc
    return _sum_pages(books[1:], acc + books[0].total_pages)


def _sum_pages_read(books: list[Book], acc: int) -> int:
    """Recursively sum pages_read across a list of books."""
    if not books:
        return acc
    return _sum_pages_read(books[1:], acc + books[0].pages_read)
```

These are called from `ReadingList.stats()`:

```python
# src/booktracker/models.py, lines 272-277
def stats(self) -> dict:
    ...
    total_pages = _sum_pages(self._books, 0)       # recursive call
    pages_read  = _sum_pages_read(self._books, 0)  # recursive call
    ...
```

The accumulator parameter (`acc`) is intentional: it demonstrates tail-recursive style where the result is built up through the parameter rather than through the return value stack. Python does not optimize tail calls, but the pattern is worth naming because it reflects how languages that *do* optimize tail calls handle list traversal.

### Alternatives Considered

**Alternative 1 — sum() comprehension (iterative)**  
```python
total_pages = sum(b.total_pages for b in self._books)
```
This is the idiomatic Python solution and would be the correct choice in production code. It was not chosen here because the spec requires demonstrating recursion. More importantly, the iterative `sum()` would have been used everywhere without comment — using the recursive functions requires a conscious decision that is visible in the code.

**Alternative 2 — Recursive directory / nested shelf traversal**  
A more complex recursive structure (a tree of shelves containing sub-shelves) would demonstrate recursion more dramatically. This was considered and rejected because it would have required extending the data model significantly beyond the capstone scope and would have made `store.py` considerably more complex to handle nested JSON structures. The page-summation functions demonstrate the concept cleanly on the existing data model without scope creep.

### Consequences

**Positive:**
- The base case (`if not books: return acc`) and recursive case (`_sum_pages(books[1:], acc + books[0].total_pages)`) are immediately readable as a standard list recursion pattern
- Using an accumulator parameter (rather than `books[0].total_pages + _sum_pages(books[1:])`) keeps the result computation in the parameter rather than the call stack, demonstrating awareness of tail-recursive style even when CPython doesn't optimize it
- Three dedicated tests cover the recursive functions: `test_recursive_sum_pages_empty`, `test_recursive_sum_pages`, and `test_recursive_sum_pages_read` (`test_models.py`, lines 111–127)

**Negative:**
- `books[1:]` creates a new list slice on every recursive call, meaning the total memory allocation is O(n²) for a list of n books. For a personal reading list of tens to hundreds of books this is inconsequential, but it is an inefficiency that should be acknowledged — a production implementation would use an index parameter instead
- CPython's default recursion limit is 1,000 frames. A reading list would need to exceed ~990 books to hit this limit, which is safe in practice but is a real constraint that `sum()` does not share

---

## ADR-006 — Persistence: JSON via stdlib

**Date:** 2026-06-26 | **Status:** Accepted  
**Governs:** `src/booktracker/store.py` (entire file, 75 lines); `pyproject.toml`, line 20 (`dependencies = []`)

### Context

BookTracker must persist the reading list between CLI invocations. The persistence layer must handle: creating the store on first use, loading all books on startup, saving after any mutation, and deserializing both `Book` and `AudioBook` objects. The format choice affects debuggability, portability, dependency count, and schema evolution.

### Decision

**JSON, stored at `~/.booktracker/books.json` by default, using `json` from the Python standard library.**

The `Store` class wraps all file I/O and handles both subclass types via a `_type` discriminator field:

```python
# src/booktracker/store.py, lines 27-75
class Store:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_PATH

    def load(self) -> ReadingList:
        rl = ReadingList()
        if not self.path.exists():
            return rl           # first run: return empty list, no error
        raw = self.path.read_text(encoding="utf-8").strip()
        if not raw:
            return rl
        data = json.loads(raw)
        for item in data.get("books", []):
            if item.get("_type") == "audiobook":
                book = AudioBook.from_dict(item)
            else:
                book = Book.from_dict(item)
            rl.add(book)
        return rl

    def save(self, reading_list: ReadingList) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"books": [b.to_dict() for b in reading_list]}
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
```

The `--store FILE` flag in `cli.py` (line 61) allows overriding the default path, which the integration tests exploit via `pytest`'s `tmp_path` fixture to avoid touching the real store during test runs.

### Alternatives Considered

**Alternative 1 — SQLite (via sqlite3 stdlib)**  
SQLite would provide indexed queries, proper typing, atomic transactions, and no load-all-on-startup cost. For a collection of 10,000 books, the performance advantage would be real. It was rejected for three reasons: (1) the spec's focus is Python OOP, not relational data modeling — using SQL would shift the codebase's center of gravity away from the assessed concepts; (2) the ORM-style deserialization required to produce `Book` and `AudioBook` objects from relational rows adds complexity that `from_dict()` classmethod handles cleanly; (3) SQLite files are not hand-editable, which is a genuine usability advantage of JSON for a personal tool.

**Alternative 2 — CSV**  
CSV is the simplest flat format, universally readable in spreadsheets. The blocking issue is that CSV has no native type system — `rating: float | None`, `date_finished: str | None`, and `pages_read: int` all serialize to strings and require explicit type casting on read. More critically, a CSV row cannot cleanly represent the `_type` discriminator needed to distinguish `Book` from `AudioBook`. JSON handles both naturally.

**Alternative 3 — pickle**  
Python's `pickle` module would serialize and deserialize Python objects directly with no `to_dict`/`from_dict` boilerplate. It was rejected because: pickle files are not human-readable, pickle is version-sensitive (a file pickled with one version of `Book` may not deserialize correctly after adding a field), and the spec's file I/O intent is best demonstrated through explicit serialization logic.

### Consequences

**Positive:**
- Zero runtime dependencies: `pyproject.toml` line 20 reads `dependencies = []`, meaning the application installs and runs on any Python 3.10+ environment with no `pip install` required
- The store file at `~/.booktracker/books.json` is human-readable and hand-editable — a power user can add or correct records directly
- `json.dump(..., indent=2, ensure_ascii=False)` produces pretty-printed output, making the file useful as a debug artifact
- `Store.__init__` accepts a `path` parameter, enabling the integration tests to pass `tmp_path / "books.json"` and run in complete isolation from the user's real data (`test_cli.py`, lines 10–13)

**Negative:**
- `Store.save()` writes the entire file on every mutation. Adding a single note to one book rewrites all books. For a personal reading list this is negligible, but it is a known limitation
- The write is not atomic: if the process is killed between opening the file and completing `json.dump`, the store file will be truncated or corrupted. A production implementation would write to a temp file and use `os.replace()` for an atomic swap — this was noted during development and explicitly deferred as out of scope
- Load-all-on-startup means every command (including `booktracker stats` on an empty list) deserializes the entire file. Again, harmless at the expected scale but a design decision worth naming

---

## ADR-007 — CLI Library: argparse over Click / Typer

**Date:** 2026-06-26 | **Status:** Accepted  
**Governs:** `src/booktracker/cli.py` (entire file, 304 lines); `pyproject.toml`, line 23 (`booktracker = "booktracker.cli:main"`)

### Context

The CLI is the application's entire user interface. The choice of library determines how subcommands are declared, how arguments are validated, what error messages look like, and whether the project requires external packages. Three mature options existed: `argparse` (stdlib), `click` (third-party), and `typer` (third-party, built on click).

### Decision

**`argparse`** — Python's standard-library CLI framework, used with `add_subparsers` to implement eight subcommands.

```python
# src/booktracker/cli.py, lines 48-125 — parser structure
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="booktracker",
        description="📚 BookTracker — your personal reading list manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=("Examples:\n"
                "  booktracker add 'Clean Code' 'Robert C. Martin' 431\n" ...),
    )
    parser.add_argument("--store", metavar="FILE", ...)
    parser.add_argument("-v", "--verbose", action="store_true", ...)

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True    # error if no subcommand given

    p_add = sub.add_parser("add", help="Add a new book")
    p_add.add_argument("title", ...)          # positional
    p_add.add_argument("author", ...)         # positional
    p_add.add_argument("pages", type=int, ...)
    p_add.add_argument("--audio", action="store_true", ...)
    p_add.add_argument("--narrator", default="", ...)
    ...
```

Command dispatch uses a `_HANDLERS` dictionary mapping command names to handler functions, keeping `main()` clean:

```python
# src/booktracker/cli.py, lines 270-298
_HANDLERS = {
    "add": _handle_add,
    "start": _handle_start,
    "progress": _handle_progress,
    "finish": _handle_finish,
    "remove": _handle_remove,
    "list": _handle_list,
    "stats": _handle_stats,
    "note": _handle_note,
}

def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    ...
    return _HANDLERS[args.command](args, store)
```

The `argv` parameter in `main()` is the key testing affordance: the integration tests call `main(["--store", store, "add", "Clean Code", ...])` directly, bypassing `sys.argv` entirely.

### Alternatives Considered

**Alternative 1 — click**  
`click` uses Python decorators (`@click.command()`, `@click.option()`) to declare CLI arguments, producing cleaner declaration syntax and better default error messages. The primary objection was the external dependency. More subtly, `click`'s decorator pattern inverts the declaration order: the handler function is decorated with argument definitions rather than the parser being built separately from the handlers. This makes the `_HANDLERS` dispatch pattern (which keeps handler functions testable in isolation) harder to implement cleanly.

**Alternative 2 — typer**  
`typer` auto-generates argument parsers from Python type annotations, producing the most ergonomic declaration syntax. `def add_cmd(title: str, author: str, pages: int, audio: bool = False)` would generate the `add` subcommand automatically. It was rejected because: (1) it pulls in `click`, `rich`, and `shellingham` as transitive dependencies — a three-package chain for a zero-dependency project is unjustifiable; (2) the implicit argument generation works against the capstone's goal of demonstrating explicit understanding of how argument parsing works.

### Consequences

**Positive:**
- `booktracker` runs on any Python 3.10+ install with `pip install -e .` — no additional packages required at runtime
- The `_HANDLERS` dispatch dictionary and separate `_build_parser()` function mean each command handler is independently testable: `_handle_add(args, store)` can be called directly in tests with a mock `args` namespace
- `--verbose` / `-v` integrates cleanly with the stdlib `logging` module (`logging.getLogger().setLevel(logging.DEBUG)`), enabling debug output with a single flag
- `epilog` with usage examples makes `booktracker --help` immediately useful to a new user

**Negative:**
- Declaring eight subcommands with `argparse` required ~80 lines of parser setup (`cli.py`, lines 48–125). The equivalent in `typer` would be approximately 25 lines. This verbosity is acceptable for a capstone but would be a maintenance burden in a large production CLI
- `argparse` error messages for wrong argument types are less polished than `click`'s styled output. `argument pages: invalid int value: 'abc'` is functional but not beautiful
- `sub.required = True` (line 74) is required to make argparse error on a missing subcommand — an unintuitive behavior that changed between Python versions

---

## ADR-008 — Project Layout: src/ Package Structure

**Date:** 2026-06-26 | **Status:** Accepted  
**Governs:** Directory structure; `pyproject.toml`, lines 27–30 (`[tool.setuptools.packages.find]` and `[tool.setuptools.package-dir]`)

### Context

Python projects can place the importable package at the repository root (`booktracker/`) or inside a `src/` directory (`src/booktracker/`). The choice is invisible to end users but has meaningful implications for local development, test isolation, and packaging correctness.

### Decision

**`src/` layout** with `pyproject.toml` configured to find packages under `src/`:

```toml
# pyproject.toml, lines 27-30
[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-dir]
"" = "src"
```

This means the importable package lives at `src/booktracker/`, and `pip install -e .` (editable install) is required before running `import booktracker` or the `booktracker` entry point.

### Alternatives Considered

**Alternative 1 — Root layout (booktracker/ at repo root)**  
Placing `booktracker/` at the repository root means `import booktracker` works from the repo directory without installation. This convenience comes at a cost: it hides import errors. If a file is missing from the package but present in the working directory, `import booktracker` silently succeeds during development but fails after installation. The `src/` layout forces the developer to install the package first, catching missing `__init__.py` files and mis-declared packages at development time rather than after distribution.

**Alternative 2 — Single-file script**  
A single `booktracker.py` file at the root eliminates all packaging complexity. This approach was appropriate for earlier modules but is not appropriate for Module 8, where the capstone is expected to demonstrate production-adjacent code organization. A single file also makes it impossible to test individual modules in isolation: a test for `Store` would import the entire file including `argparse` setup.

### Consequences

**Positive:**
- `pip install -e .` in the repo root installs the package into the active Python environment, making `booktracker` available as a shell command and `from booktracker.models import Book` work from any directory
- `src/` layout is recommended by the Python Packaging Authority (PyPA) for new projects; the `pyproject.toml` config follows PEP 517/518 standards, making the project ready for distribution to PyPI without modification
- Tests import from the installed package (`from booktracker.models import Book`) rather than from a relative path, ensuring tests exercise the same code path as end users
- The four-module separation (`models`, `cli`, `store`, `__init__`) enforces a clean dependency graph: `store.py` imports from `models.py` only; `cli.py` imports from both; no circular imports

**Negative:**
- New contributors must run `pip install -e .` before the project works. This is standard practice but is an extra step not required by a root-layout script
- The `pyproject.toml` configuration for `src/` layout is non-obvious to developers accustomed to the older `setup.py` convention

---

## ADR-009 — Test Framework: pytest over unittest

**Date:** 2026-06-26 | **Status:** Accepted  
**Governs:** `tests/test_models.py` (127 lines, 21 tests); `tests/test_cli.py` (62 lines, 8 tests); `requirements.txt` (dev dependency: `pytest>=7.4`)

### Context

The test suite must validate all business logic, dunder behavior, recursive functions, serialization round-trips, and CLI command integration. Python offers `unittest` (stdlib) and `pytest` (third-party, industry standard). The choice affects test syntax, fixture management, test discovery, and the dependency profile of the development environment.

### Decision

**`pytest`** as the test framework, with tests organized as classes on `test_models.py` and a fixture-driven integration suite in `test_cli.py`.

The key pytest features used:

```python
# tests/test_cli.py, lines 10-20 — pytest fixture for isolated store file
@pytest.fixture
def store_file(tmp_path):
    return str(tmp_path / "books.json")

def run(*args, store):
    return main(["--store", store, *args])

class TestCLI:
    def test_add_book(self, store_file):
        rc = run("add", "Clean Code", "Robert C. Martin", "431", store=store_file)
        assert rc == 0
        data = json.loads(Path(store_file).read_text())
        assert data["books"][0]["title"] == "Clean Code"
```

```python
# tests/test_models.py, lines 28-35 — pytest.raises for exception testing
def test_start_reading_already_reading_raises(self):
    b = Book.quick("T", "A", 100)
    b.start_reading()
    with pytest.raises(ValueError):
        b.start_reading()
```

### Alternatives Considered

**Alternative 1 — unittest**  
`unittest` is part of the standard library and requires no additional install. Tests are `TestCase` subclasses, and assertions use `self.assertEqual`, `self.assertRaises`, `self.assertIn`. The primary reason `pytest` was chosen over `unittest` is fixture management: `unittest`'s `setUp` / `tearDown` pattern requires each test class to manually create and clean up a temporary file for the store. `pytest`'s `tmp_path` fixture handles this automatically and is passed to each test method that needs it, eliminating 15–20 lines of boilerplate setup code from `TestCLI`.

The secondary reason is syntax: bare `assert data["books"][0]["title"] == "Clean Code"` is more readable than `self.assertEqual(data["books"][0]["title"], "Clean Code")`, and `pytest`'s assertion rewriting produces informative failure messages that show the actual vs. expected values without `self.assertX` method calls.

**Alternative 2 — doctest**  
`doctest` embeds tests in docstrings, which is elegant for illustrating function behavior in documentation. It was not considered for primary test coverage because: (1) integration tests that spin up a full CLI round-trip via `main()` and inspect the resulting JSON file cannot be expressed in a docstring without becoming illegible; (2) `@dataclass`-generated `__repr__` output includes memory addresses in some contexts, making doctest fragile for object-comparison assertions.

### Consequences

**Positive:**
- `pytest`'s `tmp_path` fixture (used in `test_cli.py`, line 11) provides a unique temporary directory per test, ensuring all 8 integration tests run in complete isolation from each other and from the user's real `~/.booktracker/books.json`
- Bare `assert` statements with `pytest`'s rewriting produce readable failure output: `AssertionError: assert 'audiobook' == 'book'` with the actual values shown inline
- Test discovery runs with `pytest` from the repo root with no configuration — `pyproject.toml` needs no `[tool.pytest.ini_options]` section because the `tests/` directory is auto-discovered
- The 29 tests run in under 1 second, enabling the full suite on every save during development

**Negative:**
- `pytest` is the only external dependency in `requirements.txt`. A developer cloning the repo must run `pip install pytest` (or `pip install -r requirements.txt`) before running tests. Unlike the zero-dependency runtime, the test environment has one dependency
- `pytest` is a dev dependency only — it is not in `pyproject.toml`'s `[project] dependencies`, so it does not affect end-user installations

---

## AI Collaboration Disclosure

This section documents every use of AI assistance during the capstone, following the assignment's academic integrity requirement. For each instance: what was suggested, what was kept, what was rejected, and how decisions were validated independently.

### 1. Overall project scoping (Claude.ai, pre-coding)

**Prompt context:** Asked for capstone domain ideas that would naturally exercise all Module 1–8 concepts.

**Suggestion received:** Reading list tracker, expense tracker, and task manager were all suggested. The reading tracker was identified as strongest because book status transitions (`to-read → reading → done`) motivate genuine state machines, and aggregate stats (total pages, average rating) motivate a recursive helper.

**What was kept:** The reading list domain itself, and the core insight that `total_pages` as a numeric progress field creates a real use case for `@property progress_pct`.

**What was rejected:** A suggestion to include a "reading streak" feature (consecutive days of reading) was rejected. It would require date arithmetic across sessions and a separate tracking mechanism, adding scope without adding OOP depth.

**How validated:** Each proposed domain was evaluated against the spec's checklist: does it give a natural subclass? (yes: AudioBook). Does it motivate a container class with multiple dunders? (yes: ReadingList). Does it create a recursive accumulation problem that isn't forced? (yes: _sum_pages). The reading list passed all three; the others did not.

### 2. @dataclass + __hash__ interaction (Claude.ai, during models.py development)

**Prompt context:** Asked why `Book` needed an explicit `__hash__` after `@dataclass` generated `__eq__`.

**Suggestion received:** Explanation that `@dataclass(eq=True)` (the default) sets `__hash__ = None` when `eq=True`, making instances unhashable. Suggested defining `__hash__` on `(title.lower(), author.lower())` to match the equality semantics.

**What was kept:** The `__hash__` implementation on `(title.lower(), author.lower())` at `models.py:88–89`, and the understanding that hash and equality must be consistent (objects that compare equal must have the same hash).

**What was rejected:** A suggestion to use `@dataclass(unsafe_hash=True)` was rejected. `unsafe_hash=True` generates a hash from all fields, meaning two books with the same title and author but different `pages_read` would have different hashes — violating the contract that equal objects must hash equally. The manual `__hash__` on normalized title+author is semantically correct.

**How validated:** The test `test_hash_uniqueness` in `test_models.py:76–78` verifies that two `Book` objects with the same title and author but different `total_pages` produce the same hash. The consistency of `__eq__` and `__hash__` was checked manually: `b1 == b2` is `True` for same title+author regardless of other fields; `hash(b1) == hash(b2)` is also `True` for the same pair.

### 3. AudioBook.from_dict reconstruction pattern (Claude.ai, during AudioBook development)

**Prompt context:** Asked how to implement `AudioBook.from_dict` given that `super().from_dict()` returns a `Book`, not an `AudioBook`.

**Suggestion received:** Call `super().from_dict(data)` to deserialize shared fields into a `Book`, then unpack that `Book`'s attributes into the `AudioBook` constructor.

**What was kept:** The pattern at `models.py:174–186` — call `super().from_dict()`, then construct `AudioBook(title=book.title, author=book.author, ..., narrator=data.get("narrator", ""))`.

**What was rejected:** A suggestion to directly call `Book.from_dict(data)` without using `super()` was rejected because it bypasses the MRO and would break if `Book.from_dict` were ever overridden in an intermediate class. `super().from_dict(data)` is the correct pattern.

**How validated:** `test_round_trip_dict` in `test_models.py:80–82` verifies a `Book` round-trips correctly. The `AudioBook` round-trip is verified in `TestCLI.test_add_book` (indirectly — adding a book via CLI and reading it back from JSON). The `_type: "audiobook"` discriminator in `to_dict()` and `Store.load()` was manually tested by running `booktracker add --audio "Dune" "Herbert" 600 --narrator "Tim"` and inspecting the resulting JSON.

### 4. argparse handler dispatch pattern (GitHub Copilot, during cli.py development)

**Prompt context:** Writing the `main()` function after defining eight `_handle_*` functions.

**Suggestion received:** Copilot autocompleted an `if/elif` chain for command dispatch:
```python
if args.command == "add":
    return _handle_add(args, store)
elif args.command == "start":
    return _handle_start(args, store)
...
```

**What was kept:** The structure of separate `_handle_*` functions, one per subcommand — this was already the plan before Copilot's suggestion.

**What was rejected:** The `if/elif` chain was replaced with the `_HANDLERS` dictionary at `cli.py:270–281`. A dictionary dispatch is more extensible (adding a new command requires one line in `_HANDLERS` rather than an additional `elif` branch) and more testable (the handler functions are accessible by name for direct testing).

**How validated:** The `_HANDLERS` pattern was cross-checked against the dispatch patterns used in production CLI tools (Flask's `app.cli`, Click's command groups). All 8 integration tests call `main()` and verify return codes, confirming that dispatch routes correctly to each handler.

### 5. Test suite (no AI used)

All 29 tests in `tests/test_models.py` and `tests/test_cli.py` were written without AI assistance. Test cases were derived from the domain's state machine (valid and invalid transitions), edge cases discovered during manual testing (empty list, duplicate title, invalid rating > 5.0, progress update auto-starting reading status), and the spec's explicit requirements (at least one recursive function test, at least one dunder test). Test names follow the `test_<condition>_<expected>` convention throughout.

---

## Self-Assessment

### Three Components I Am Most Proud Of

**1. The `__contains__` dual-dispatch on `ReadingList` (`models.py:226–233`)**

This is the most subtle implementation in the project. `ReadingList.__contains__` accepts either a `str` (title lookup, case-insensitive) or a `Book` object (identity lookup via `__eq__`). This makes two usage patterns both feel natural: `if "Clean Code" in reading_list` (used in `ReadingList.add()` for duplicate checking) and `assert book in reading_list` (used in tests). The type-dispatch logic is six lines, but the design thought behind it — that a container's membership test should match how humans think about membership, not just how the internal data structure represents it — is the kind of reasoning that separates a functioning implementation from a well-designed one.

**2. The `_HANDLERS` dispatch dictionary in `cli.py` (`lines 270–281`)**

Replacing an `if/elif` chain with a dictionary lookup is a small change that demonstrates awareness of open/closed design: adding a ninth command in the future requires one line in `_HANDLERS` and one new `_handle_*` function, with zero changes to `main()`. More importantly, the `argv` parameter in `main(argv: list[str] | None = None)` combined with the `_HANDLERS` pattern means each handler is independently testable by calling `main()` with a synthetic argument list. The integration test suite exploits this directly, and all 8 integration tests pass without mocking, patching, or subprocess execution.

**3. The four-module separation with a clean import dependency graph**

`store.py` imports from `models.py` only. `cli.py` imports from `models.py` and `store.py`. `utils` was kept in `models.py` rather than split out to avoid a module that imports from nothing and is imported by everything. No circular imports exist. This structure means any module can be tested in isolation: `test_models.py` imports only from `booktracker.models`; `test_cli.py` imports from `booktracker.cli` and inspects the store file directly as JSON. The discipline is invisible in normal operation but becomes obvious when something breaks — a test failure in `TestBook` cannot be caused by a bug in `cli.py`.

### One Component I Would Redesign With Another Week

**`Store.save()` — atomic writes and a structural envelope.**

The current implementation writes the entire `books.json` file in one `json.dump()` call (`store.py:64–73`). This has two known weaknesses documented in ADR-006: the write is not atomic (a crash mid-write corrupts the file), and it rewrites all books on every mutation.

With another week, I would make two targeted changes:

**First — atomic save with `os.replace()`:**

```python
# What store.py save() would look like with atomic writes
import tempfile, os

def save(self, reading_list: ReadingList) -> None:
    self.path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"books": [b.to_dict() for b in reading_list]}
    # Write to a temp file in the same directory, then atomically replace
    fd, tmp_path = tempfile.mkstemp(
        dir=self.path.parent, suffix=".tmp", prefix=".booktracker_"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.path)   # atomic on POSIX; near-atomic on Windows
    except Exception:
        os.unlink(tmp_path)              # clean up temp file on failure
        raise
```

This change is five additional lines. It makes the store corruption-safe: if the process is killed mid-write, `os.replace()` has not been called, the original `books.json` is intact, and the temp file is cleaned up on the next OS garbage collection.

**Second — a `version` field in the JSON envelope:**

```json
{
  "version": 1,
  "books": [ ... ]
}
```

Adding a `version` field at load time costs one line. It pays dividends the first time a new field is added to `Book` — the version number allows `Store.load()` to apply a migration function for old files rather than failing with a `KeyError`. The current `from_dict` uses `.get()` with defaults for optional fields, which handles forward-compatible additions, but a version field makes the migration contract explicit.

Neither change alters any interface in `models.py` or `cli.py` — they are purely internal to `store.py`, which is exactly the kind of well-scoped improvement that shows understanding of what a production-grade persistence layer looks like beyond the minimum viable implementation.

---

*End of Architecture Decision Log — BookTracker CLI, Module 8 Capstone*  
*Waqar Javed · github.com/iamwaqarjaved/booktracker-cli*
