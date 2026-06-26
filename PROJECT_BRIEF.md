# Project Brief — BookTracker CLI

## What Does It Do?

BookTracker is a command-line personal reading list manager. It lets a reader
add books, update their reading progress, record ratings and notes, and view
statistics about their reading habits — all persisted locally as JSON.

## Who Uses It?

Any developer or technically comfortable reader who prefers the terminal over
GUI apps and wants a lightweight, no-account, no-cloud reading log they fully
control.

## Smallest Version That Proves the Concept

1. Add a book (title, author, total pages)
2. Start/finish the book (status transitions: `to-read → reading → done`)
3. Update pages read
4. List all books with a summary table
5. View stats (total books, pages read, average rating)
6. Data persists between runs via a local JSON file

Everything else (genres, notes, shell autocomplete) is a stretch goal that
does NOT appear in v1.0.

## Success Criteria

- `pip install -e .` works from a fresh clone
- `booktracker --help` prints a useful help message
- A new user can add and finish a book in under 60 seconds
- The JSON store is human-readable and hand-editable
- All five week-1–8 concept areas are exercised (see Architecture Decision Log)
