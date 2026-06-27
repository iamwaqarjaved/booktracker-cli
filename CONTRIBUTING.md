# Contributing to BookTracker CLI

Thank you for your interest in contributing! This is a Python learning project
built as a Module 8 capstone, and contributions of all sizes are welcome —
bug fixes, new commands, documentation improvements, or additional tests.

---

## Quick start

```bash
# 1. Fork the repo on GitHub, then clone your fork
git clone https://github.com/<your-username>/booktracker-cli.git
cd booktracker-cli

# 2. Install in editable mode
pip install -e .

# 3. Install test dependencies
pip install pytest

# 4. Verify everything passes before making changes
python -m pytest tests/ -v
# Expected: 29 passed
```

---

## Project structure

```
src/booktracker/
├── models.py   # Domain objects: Book, AudioBook, ReadingList, recursive helpers
├── store.py    # JSON persistence (Store class)
├── cli.py      # argparse parser + command handlers + main()
└── __init__.py

tests/
├── test_models.py   # 21 unit tests
└── test_cli.py      # 8 integration tests (use tmp_path fixture)
```

**Dependency rule:** `models.py` must never import from `store.py` or `cli.py`.
`store.py` may import from `models.py` only. `cli.py` imports from both.
No circular imports.

---

## Making changes

### Fixing a bug

1. Open an issue describing the bug (or comment on an existing one)
2. Create a branch: `git checkout -b fix/describe-the-bug`
3. Write a failing test that reproduces the bug
4. Fix the code until the test passes
5. Run the full suite: `python -m pytest tests/ -v`
6. Open a pull request

### Adding a new command

New commands follow this pattern:

1. Add a subparser in `cli.py → _build_parser()`
2. Write a `_handle_<command>(args, store)` function
3. Register it in the `_HANDLERS` dictionary
4. Add at least one integration test in `tests/test_cli.py`

Example skeleton:

```python
# In _build_parser():
p_export = sub.add_parser("export", help="Export list to CSV")
p_export.add_argument("--output", default="books.csv", help="Output filename")

# New handler:
def _handle_export(args, store: Store) -> int:
    rl = store.load()
    # ... write CSV ...
    print(f"✅  Exported {len(rl)} books to {args.output}")
    return 0

# In _HANDLERS:
_HANDLERS = {
    ...
    "export": _handle_export,
}
```

---

## Testing guidelines

- **Unit tests** go in `test_models.py` — test a single class or function in isolation
- **Integration tests** go in `test_cli.py` — call `main()` with a `--store tmp_path` file
- Use `pytest.raises(SomeError)` for expected exceptions
- Test names follow `test_<condition>_<expected_outcome>`
- Every new feature needs at least one test; every bug fix needs a regression test

---

## Code style

- Python 3.10+ syntax (`str | None` unions, `match/case` if appropriate)
- Type annotations on all public functions and methods
- Docstrings on all public classes and methods (one-liner is fine for simple methods)
- No external runtime dependencies — `dependencies = []` in `pyproject.toml` must stay empty

---

## Commit message format

```
<type>: <short description>

<optional body>
```

Types: `fix`, `feat`, `docs`, `test`, `refactor`, `chore`

Examples:
```
feat: add export command for CSV output
fix: handle empty store file without crashing
docs: update TUTORIAL with extension ideas
test: add regression test for duplicate audiobook add
```

---

## Opening a pull request

- Target the `main` branch
- Fill in the PR template (all 29 tests must pass)
- If your change involves a significant design decision, add an ADR to `docs/ADL.md`
- Keep PRs focused — one feature or fix per PR

---

## Questions?

Open a GitHub Discussion or file an issue with the `question` label.
