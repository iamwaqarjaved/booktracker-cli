"""Tests for models.py"""
import pytest
from booktracker.models import (
    AudioBook, Book, ReadingList,
    TO_READ, READING, DONE,
    _sum_pages, _sum_pages_read,
)


# ── Book ──────────────────────────────────────
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
            b.start_reading()

    def test_finish(self):
        b = Book.quick("T", "A", 100)
        b.start_reading()
        b.finish(rating=4.0)
        assert b.status == DONE
        assert b.rating == 4.0
        assert b.pages_read == 100

    def test_finish_invalid_rating(self):
        b = Book.quick("T", "A", 100)
        b.start_reading()
        with pytest.raises(ValueError):
            b.finish(rating=6.0)

    def test_update_progress_auto_starts(self):
        b = Book.quick("T", "A", 100)
        b.update_progress(10)
        assert b.status == READING

    def test_lt_sorting(self):
        a = Book.quick("Zebra", "Author", 100)
        b = Book.quick("Apple", "Author", 100)
        assert b < a

    def test_hash_uniqueness(self):
        b1 = Book.quick("Title", "Author", 100)
        b2 = Book.quick("Title", "Author", 200)
        assert hash(b1) == hash(b2)   # same title+author

    def test_round_trip_dict(self):
        b = Book.quick("Round Trip", "Tester", 50)
        assert Book.from_dict(b.to_dict()).title == "Round Trip"


# ── AudioBook ─────────────────────────────────
class TestAudioBook:
    def test_str_contains_headphones(self):
        ab = AudioBook("Dune", "Herbert", 600, narrator="Tim")
        assert "🎧" in str(ab)

    def test_to_dict_type(self):
        ab = AudioBook("Dune", "Herbert", 600)
        assert ab.to_dict()["_type"] == "audiobook"


# ── ReadingList ───────────────────────────────
class TestReadingList:
    def _list_with_books(self):
        rl = ReadingList()
        rl.add(Book.quick("A", "Auth1", 100))
        rl.add(Book.quick("B", "Auth2", 200))
        return rl

    def test_len(self):
        rl = self._list_with_books()
        assert len(rl) == 2

    def test_contains_string(self):
        rl = self._list_with_books()
        assert "A" in rl

    def test_iter(self):
        rl = self._list_with_books()
        titles = [b.title for b in rl]
        assert titles == ["A", "B"]

    def test_duplicate_raises(self):
        rl = ReadingList()
        rl.add(Book.quick("X", "Y", 10))
        with pytest.raises(ValueError):
            rl.add(Book.quick("X", "Z", 20))

    def test_remove(self):
        rl = self._list_with_books()
        rl.remove("A")
        assert len(rl) == 1

    def test_stats_pages(self):
        rl = self._list_with_books()
        s = rl.stats()
        assert s["total_pages_in_list"] == 300


# ── Recursive helpers ─────────────────────────
def test_recursive_sum_pages_empty():
    assert _sum_pages([], 0) == 0

def test_recursive_sum_pages():
    books = [Book.quick("A", "X", 10), Book.quick("B", "Y", 20)]
    assert _sum_pages(books, 0) == 30

def test_recursive_sum_pages_read():
    b1 = Book.quick("A", "X", 100)
    b1.pages_read = 40
    b2 = Book.quick("B", "Y", 100)
    b2.pages_read = 60
    assert _sum_pages_read([b1, b2], 0) == 100
