# Architecture Decision Log (ADL)
## BookTracker CLI — Module 8 Capstone

---

### ADL-001 · Domain Choice: Reading List Manager

**Date:** 2026-06-26  
**Status:** Accepted

**Context**  
The capstone requires a CLI app that naturally exercises every concept from
weeks 1–8 without forcing constructs.

**Decision**  
Use a personal reading list tracker. Books are real domain objects with clear
state transitions (`to-read → reading → done`), naturally calling for a class
model, persistence, and user-facing commands.

**Rationale**  
- Non-trivial but fully understandable in 2 minutes — good for hiring-manager demos  
- Stateful objects (status, pages_read) justify `@property` and instance methods  
- A list of books is the natural container class (`ReadingList`) with `__len__`,
  `__iter__`, `__contains__`  
- Aggregate stats (total pages, average rating) invite a recursive helper as a
  deliberate teaching moment

**Rejected alternatives**  
- Task/todo manager — too common; weaker O-level differentiation  
- Expense tracker — numbers-only; doesn't benefit from inheritance  

---

### ADL-002 · `@dataclass` for Book, plain class for ReadingList

**Date:** 2026-06-26  
**Status:** Accepted

**Context**  
`@dataclass` auto-generates `__init__`, `__repr__`, and `__eq__` from field
declarations, removing boilerplate for simple value objects.

**Decision**  
`Book` and `AudioBook` are `@dataclass`s. `ReadingList` is a plain class because it
has mutable container state and custom dunder semantics that don't map to
dataclass defaults.

**Consequence**  
`Book` needs an explicit `__hash__` because `@dataclass(eq=True)` (the default)
sets `__hash__ = None` when `eq=True`. We define `__hash__` on `(title, author)`.

---

### ADL-003 · Inheritance: AudioBook extends Book

**Date:** 2026-06-26  
**Status:** Accepted

**Context**  
The spec requires at least one inheritance relationship.

**Decision**  
`AudioBook(Book)` adds a `narrator` field and overrides `__str__` and
`from_dict`/`to_dict` to tag the JSON record as `_type: audiobook`.

**Rationale**  
Audiobooks *are* books with extra metadata; inheritance is semantically honest.
The store discriminates on `_type` to reconstruct the right subclass.

**Consequence**  
`AudioBook.from_dict` calls `super().from_dict()`, which returns a plain `Book`.
We then unpack that `Book` into an `AudioBook` constructor. This is a documented
pattern for `@dataclass` inheritance with `from_dict`.

---

### ADL-004 · Recursive page summation

**Date:** 2026-06-26  
**Status:** Accepted

**Context**  
The spec requires at least one recursive function used *naturally*.

**Decision**  
`_sum_pages(books, acc)` and `_sum_pages_read(books, acc)` recursively accumulate
page counts with an accumulator pattern (tail-recursive in spirit).

**Rationale**  
Python doesn't optimise tail calls, but the lists are short (personal reading
lists rarely exceed a few hundred books) so stack depth is never a concern.
Recursion here illustrates the concept cleanly without being forced.

**Rejected alternatives**  
- Recursive directory walk — not relevant to the domain  
- Recursive JSON merging — would require an artificial sub-list concept  

---

### ADL-005 · JSON persistence, stdlib only

**Date:** 2026-06-26  
**Status:** Accepted

**Context**  
The spec requires file I/O persistence. Options: JSON, CSV, SQLite,
third-party ORM.

**Decision**  
`json` from the standard library; store defaults to `~/.booktracker/books.json`.

**Rationale**  
- Zero external runtime dependencies → `pip install -e .` works offline  
- Human-readable and hand-editable (good for power users)  
- Portable: same file works across macOS, Linux, Windows  

**Consequence**  
Concurrent writes are not safe; acceptable for a single-user CLI tool.

---

### ADL-006 · `argparse` over third-party CLIs (Click, Typer)

**Date:** 2026-06-26  
**Status:** Accepted

**Context**  
Click and Typer offer decorator-driven CLIs with less boilerplate.

**Decision**  
Use `argparse` (stdlib).

**Rationale**  
- Zero external dependencies  
- Directly maps to the course requirement  
- `--help` is auto-generated and professional-looking  

---

### ADL-007 · `src/` layout

**Date:** 2026-06-26  
**Status:** Accepted

**Context**  
Python projects can place packages at the repo root or inside a `src/`
directory.

**Decision**  
Use `src/booktracker/` layout with `pyproject.toml` pointing
`tool.setuptools.packages.find.where = ["src"]`.

**Rationale**  
- `src/` layout prevents accidental imports of the un-installed package from
  the repo root — catches missing `__init__.py` files early  
- Matches modern Python packaging best practices (PyPA guide)  

---

### ADL-008 · Dunder inventory (Week 8 requirement)

The following table maps each required dunder to its location and purpose.

| Dunder | Class | Purpose |
|---|---|---|
| `__init__` | `Book` (via @dataclass) | Field initialisation |
| `__repr__` | `Book` (via @dataclass), `ReadingList` | Unambiguous debug string |
| `__str__` | `Book`, `AudioBook`, `ReadingList` | Human-readable one-liner |
| `__eq__` | `Book` (via @dataclass) | Value equality on all fields |
| `__lt__` | `Book` | Enables `sorted(books)` by title |
| `__hash__` | `Book` | Set / dict key on title+author |
| `__len__` | `ReadingList` | `len(rl)` → book count |
| `__contains__` | `ReadingList` | `'title' in rl` by string or Book |
| `__iter__` | `ReadingList` | `for book in rl:` |

Total: 9 dunder methods (spec minimum: 5). ✅
