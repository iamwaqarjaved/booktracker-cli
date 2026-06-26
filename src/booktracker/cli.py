"""
cli.py
------
Command-line interface for BookTracker using argparse.

Sub-commands
~~~~~~~~~~~~
  add       Add a new book
  start     Mark a book as currently reading
  progress  Update pages read
  finish    Mark a book as done (with optional rating)
  remove    Delete a book from the list
  list      Print all books (filterable by status)
  stats     Print aggregate reading statistics
  note      Append a note to a book

Usage examples
~~~~~~~~~~~~~~
  booktracker add "Clean Code" "Robert C. Martin" 431
  booktracker start "Clean Code"
  booktracker progress "Clean Code" 200
  booktracker finish "Clean Code" --rating 4.5
  booktracker list --status done
  booktracker stats
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from booktracker.models import VALID_STATUSES, AudioBook, Book
from booktracker.store import Store

# ── logging setup ──────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Argument parser
# ──────────────────────────────────────────────
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
    parser.add_argument(
        "--store",
        metavar="FILE",
        help="Path to the JSON store file (default: ~/.booktracker/books.json)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # ── add ──
    p_add = sub.add_parser("add", help="Add a new book")
    p_add.add_argument("title", help="Book title (quote if multi-word)")
    p_add.add_argument("author", help="Author name")
    p_add.add_argument("pages", type=int, help="Total pages (or minutes for audiobooks)")
    p_add.add_argument("--audio", action="store_true", help="Treat as audiobook")
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
    p_fin.add_argument("--rating", type=float, metavar="0-5",
                       help="Star rating (0.0–5.0)")

    # ── remove ──
    p_rem = sub.add_parser("remove", help="Remove a book from the list")
    p_rem.add_argument("title", help="Book title")

    # ── list ──
    p_list = sub.add_parser("list", help="List books")
    p_list.add_argument(
        "--status",
        choices=VALID_STATUSES,
        default=None,
        help="Filter by status",
    )
    p_list.add_argument("--sort", action="store_true", help="Sort alphabetically")

    # ── stats ──
    sub.add_parser("stats", help="Show reading statistics")

    # ── note ──
    p_note = sub.add_parser("note", help="Add a note to a book")
    p_note.add_argument("title", help="Book title")
    p_note.add_argument("text", help="Note text to append")

    return parser


# ──────────────────────────────────────────────
# Command handlers
# ──────────────────────────────────────────────
def _handle_add(args, store: Store) -> int:
    rl = store.load()
    if args.audio:
        book = AudioBook(
            title=args.title,
            author=args.author,
            total_pages=args.pages,
            narrator=args.narrator,
        )
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
        books = sorted(books)

    if not books:
        print(f"No books with status '{args.status}'.")
        return 0

    # Table header
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
        title_disp = b.title[:col["title"] - 1] if len(b.title) > col["title"] - 1 else b.title
        author_disp = b.author[:col["author"] - 1] if len(b.author) > col["author"] - 1 else b.author
        print(
            f"{title_disp:<{col['title']}} {author_disp:<{col['author']}} "
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


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
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

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    store = Store(path=args.store if args.store else None)

    handler = _HANDLERS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args, store)
    except Exception as exc:          # pylint: disable=broad-except
        logger.exception("Unexpected error")
        print(f"💥  Unexpected error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
