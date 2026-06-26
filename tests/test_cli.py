"""Integration tests for the CLI."""
import json
import tempfile
from pathlib import Path

import pytest
from booktracker.cli import main


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

    def test_duplicate_add_fails(self, store_file):
        run("add", "Dupe", "Author", "100", store=store_file)
        rc = run("add", "Dupe", "Author", "100", store=store_file)
        assert rc == 1

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
        rc = run("list", store=store_file)
        assert rc == 0

    def test_stats(self, store_file):
        rc = run("stats", store=store_file)
        assert rc == 0

    def test_note(self, store_file):
        run("add", "NoteBook", "Author", "50", store=store_file)
        rc = run("note", "NoteBook", "Great opening chapter!", store=store_file)
        assert rc == 0
        data = json.loads(Path(store_file).read_text())
        assert "Great opening chapter!" in data["books"][0]["notes"]

    def test_remove(self, store_file):
        run("add", "ToRemove", "X", "10", store=store_file)
        rc = run("remove", "ToRemove", store=store_file)
        assert rc == 0
