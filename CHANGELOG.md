# Changelog

All notable changes to BookTracker CLI are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-06-27

### Added

- `booktracker add` — add a regular book or audiobook (`--audio --narrator`)
- `booktracker start` — mark a book as currently reading
- `booktracker progress` — update pages read (auto-starts reading if status is `to-read`)
- `booktracker finish` — mark a book as done with optional star rating (0.0–5.0)
- `booktracker remove` — delete a book from the list
- `booktracker list` — display all books in a formatted table; filter by `--status`; sort alphabetically with `--sort`
- `booktracker stats` — aggregate statistics: total books, pages read, average rating
- `booktracker note` — append a text note to a book
- `--store FILE` global flag to override the default store path (`~/.booktracker/books.json`)
- `-v / --verbose` global flag to enable DEBUG-level logging
- JSON persistence at `~/.booktracker/books.json` — human-readable, hand-editable, zero external dependencies
- `AudioBook` subclass with `narrator` field and 🎧 display indicator
- `@property progress_pct` — live percentage of pages read
- `ReadingList` container with `__len__`, `__iter__`, `__contains__` dunders
- `Book.__lt__` enabling `sorted(books)` alphabetically by title
- `Book.__hash__` on `(title.lower(), author.lower())` for set/dict support
- Recursive `_sum_pages` and `_sum_pages_read` helpers with accumulator pattern
- 29 passing tests (21 unit + 8 integration) via `pytest`
- `src/` layout with `pyproject.toml` PEP 517 build config
- GitHub Actions CI across Python 3.10, 3.11, 3.12
- Architecture Decision Log (`docs/ADL.md`) — 9 ADRs documenting every significant design decision
- Step-by-step build tutorial (`docs/TUTORIAL.md`)

---

## Unreleased

### Planned

- Shell tab-completion for book titles
- `booktracker export --csv` to export the reading list
- `booktracker import` to bulk-add books from a CSV file
- `--genre` field on `Book` with `list --genre` filter
- Atomic writes in `Store.save()` using `tempfile` + `os.replace()`
- Reading goal tracking (yearly page target) in `stats`
