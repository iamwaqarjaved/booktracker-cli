# AI Collaboration Appendix — Transparency and Reproducibility

**Course:** CIT 411 — Applied Generative AI  
**Module:** 8 · Capstone — Methods, Dunder Methods, and Integration  
**Project:** BookTracker CLI  
**Author:** Waqar Javed  
**Date:** June 2025  
**Repository:** `docs/AI_COLLABORATION.md`  
**Cross-reference:** `docs/ADL.md` (Architecture Decision Log)

---

## 1. AI Tools Catalog

| Tool | Version / Tier | Primary Use | Frequency |
|---|---|---|---|
| Claude (Anthropic) | Claude Sonnet (claude.ai Pro) | Architecture design, code review, debugging, documentation drafting | High — consulted throughout all phases |
| GitHub Copilot | Free tier (VS Code extension) | Inline autocompletion for boilerplate patterns | Low — occasionally accepted, often ignored |

**Note on scope:** GitHub Copilot suggestions were largely incidental and not actively solicited for design decisions. Claude was the primary AI collaborator and the tool whose outputs required the most deliberate evaluation and editing.

---

## 2. Prompt Catalog by Component

Prompts are organized by the capstone component they informed. Prompts were conversational — meaning each built on prior context — but the significant ones are isolated below by intent.

---

### 2.1 Architecture Decisions

**Prompt A-1 — Initial scope framing:**
> "I'm building a BookTracker CLI in Python for a capstone. It needs to track books with status (reading/completed/want-to-read), support adding, listing, updating, and deleting entries, use dataclasses, demonstrate dunder methods, and have a recursive search function. Help me think through the architecture before I write any code."

**Purpose:** Establish the overall module structure before committing to a design.  
**AI Output:** Suggested a two-class hierarchy (`Book` base class → `TrackedBook` subclass), a `BookTracker` manager class, and a `FileHandler` utility. Recommended `argparse` for the CLI layer and `json` for persistence.  
**My Disposition:** Kept the two-class hierarchy and argparse recommendation. Rejected the `FileHandler` as a separate class — I consolidated file I/O into `BookTracker` directly to reduce indirection. This was an intentional simplification.

---

**Prompt A-2 — Deciding where dunder methods belong:**
> "Should `__str__`, `__repr__`, and `__eq__` live on Book or TrackedBook? And should `__len__` go on BookTracker or Book?"

**AI Output:** Recommended `__str__`/`__repr__`/`__eq__` on `Book` (for the entity), and `__len__` on `BookTracker` (for the collection). Also suggested `__contains__` on `BookTracker` for membership testing.  
**My Disposition:** Accepted the placement rationale — it matched the principle of assigning behavior to the object that owns the data. Added `__contains__` to `BookTracker` after the explanation made the use case clear.

---

**Prompt A-3 — Recursive search design:**
> "The assignment requires a recursive function. My data is a flat list of books. What's a meaningful recursive implementation that isn't artificially forced?"

**AI Output:** Proposed recursive binary search over a sorted list, or recursive filtering across a nested genre hierarchy. Also suggested recursive mergesort as an alternative.  
**My Disposition:** Rejected binary search (required sorted input, added complexity that didn't serve the user). Adopted recursive linear search/filter — I redesigned it to recurse over a list slice (`books[1:]`) with a base case of empty list, searching by title substring. This felt honest to the data structure rather than contrived.

---

### 2.2 Class and Method Design

**Prompt B-1 — Dataclass field design for `Book`:**
> "What fields should Book have as a dataclass, and which should have defaults? I want to use `field()` for at least one."

**AI Output:** Suggested `title`, `author`, `genre` (with `field(default='Unknown')`), `isbn` (optional), and `year` (optional int).  
**My Disposition:** Kept `title`, `author`, `genre` with the default. Dropped `isbn` — added unnecessary complexity without adding user value. Added `year` as an optional int with `field(default=None)`.

---

**Prompt B-2 — Inheritance and method override:**
> "TrackedBook extends Book. What should it add, and should any Book methods be overridden?"

**AI Output:** Suggested `status` and `date_added` fields on `TrackedBook`. Recommended overriding `__str__` to include status in the display string.  
**My Disposition:** Accepted both. Wrote the override myself — the AI's suggested string format included ANSI color codes, which I removed since terminal color support is inconsistent and wasn't part of the spec.

---

**Prompt B-3 — `__eq__` implementation:**
> "How should I implement `__eq__` on Book? Should it compare all fields or just title+author?"

**AI Output:** Recommended title + author comparison (case-insensitive) as the semantic identity of a book, and warned that ISBN-based equality is unreliable when ISBN is optional.  
**My Disposition:** Accepted the design rationale. Implemented it myself using `.lower().strip()` normalization.

---

### 2.3 Recursive Function Implementation

**Prompt C-1 — Recursive search structure:**
> "Show me a skeleton of a recursive book search — I want to write the actual logic myself but see the shape of the recursion."

**AI Output:** Provided a skeleton with base case (`if not books: return []`), match check, and recursive call on `books[1:]`.  
**My Disposition:** Used the structural skeleton as a starting reference but wrote all match logic, parameter signature, and return type handling myself. The final implementation differs in how partial matches are accumulated.

---

**Prompt C-2 — Avoiding recursion limit issues:**
> "Python's default recursion limit is 1000. My book list could theoretically exceed that. How should I handle this?"

**AI Output:** Suggested `sys.setrecursionlimit()` or converting to iteration for production, but noted that for a CLI tool with a JSON file backend, practical list sizes make this a non-issue worth documenting rather than engineering around.  
**My Disposition:** Accepted the reasoning. Added a docstring comment noting the theoretical limit and that iterative implementation would be preferred in a production context. Did not add `setrecursionlimit` — it would obscure the real lesson.

---

### 2.4 File I/O and Persistence

**Prompt D-1 — JSON persistence design:**
> "What's the cleanest way to serialize and deserialize dataclass instances to JSON without a heavy library?"

**AI Output:** Showed `dataclasses.asdict()` for serialization and manual reconstruction via `TrackedBook(**data)` for deserialization. Also mentioned `dacite` and `marshmallow` as alternatives.  
**My Disposition:** Used `dataclasses.asdict()` approach — it was clean and had no external dependencies. Rejected third-party libraries; this is a coursework project and keeping the dependency surface minimal was a deliberate choice.

---

**Prompt D-2 — Error handling for missing file:**
> "What should happen if the JSON file doesn't exist on first run?"

**AI Output:** Suggested catching `FileNotFoundError` and initializing with an empty list; also suggested creating the file on first save rather than on startup.  
**My Disposition:** Accepted: create file on first write, not on startup. Wrote the exception handler myself.

---

### 2.5 CLI Interface (`argparse`)

**Prompt E-1 — Subparser structure:**
> "I need subcommands: add, list, update, delete, search. Show me the argparse subparser skeleton."

**AI Output:** Provided a full argparse skeleton with `add_subparsers()`, individual `add_parser()` calls, and argument definitions for each subcommand.  
**My Disposition:** Used the skeleton as a structural guide. Rewrote the argument names and help strings entirely — the AI's defaults were generic (`--name`, `--value`) and I replaced them with domain-appropriate names (`--title`, `--author`, `--status`). Added a `--year` flag the AI didn't include.

---

**Prompt E-2 — Handling required vs. optional args:**
> "For the `update` subcommand, should all fields be optional (only update what's provided) or should I require the full record?"

**AI Output:** Strongly recommended partial updates (all fields optional, update only what's provided). Explained this is standard CLI UX.  
**My Disposition:** Accepted. This also shaped how I wrote the `update()` method on `BookTracker` — only passed fields that were not `None`.

---

### 2.6 Testing

**Prompt F-1 — Test organization:**
> "I have 29 tests passing. How should I organize them across test files for a project this size?"

**AI Output:** Suggested one test file per module (`test_book.py`, `test_tracker.py`, `test_cli.py`) and grouping tests by method within each file.  
**My Disposition:** Adopted the three-file structure. Did not follow all of the AI's suggested test names — wrote my own test cases from scratch based on the actual behavior I needed to verify.

---

**Prompt F-2 — Testing file I/O without touching real files:**
> "How do I test save/load without creating real files on disk?"

**AI Output:** Recommended `unittest.mock.patch` with `mock_open` for unit tests, or `tempfile.NamedTemporaryFile` for integration tests.  
**My Disposition:** Used `tempfile` for integration tests — `mock_open` felt like testing the mock rather than the behavior. Wrote all test methods myself.

---

### 2.7 README and Documentation

**Prompt G-1 — README structure:**
> "What sections should a professional README for a CLI tool include?"

**AI Output:** Suggested: Project title, description, installation, usage (with subcommand examples), architecture overview, running tests, and license.  
**My Disposition:** Used this as the section skeleton. Wrote all content myself. Added a "Design Decisions" section the AI didn't suggest, linking to `docs/ADL.md`.

---

**Prompt G-2 — Docstring style:**
> "Should I use Google-style, NumPy-style, or reStructuredText docstrings?"

**AI Output:** Recommended Google-style for a project this size — readable without tooling, widely recognized.  
**My Disposition:** Accepted. Applied Google-style throughout all public methods.

---

## 3. Output Dispositions Summary

| Prompt | What Was Kept | What Was Edited | What Was Rejected | Why |
|---|---|---|---|---|
| A-1 (Architecture) | Two-class hierarchy, argparse, JSON | — | Separate `FileHandler` class | Added indirection without benefit |
| A-2 (Dunders) | Placement rationale for all methods | — | None | Sound object-oriented reasoning |
| A-3 (Recursion) | Recursive slice pattern concept | Design to recurse over list slice | Binary search, mergesort | Forced fit to flat data structure |
| B-1 (Fields) | `title`, `author`, `genre` with default | Added `year`, removed `isbn` | `isbn` | Unnecessary complexity for scope |
| B-2 (Inheritance) | `status`, `date_added`, override of `__str__` | Removed ANSI color codes | Color formatting | Terminal compatibility concern |
| B-3 (`__eq__`) | Title + author semantic identity | Wrote implementation myself | — | |
| C-1 (Recursion skeleton) | Base case / recursive call structure | All match logic, signature, return handling | — | Only used structural shape |
| C-2 (Recursion limit) | Docstring comment approach | — | `setrecursionlimit()` | Obscures the lesson |
| D-1 (JSON persistence) | `dataclasses.asdict()` approach | — | Third-party libraries | Minimal dependency preference |
| D-2 (Missing file) | Create on first write | Wrote handler myself | — | |
| E-1 (argparse skeleton) | Subparser structure | All argument names and help strings | Generic names | Domain specificity required |
| E-2 (Partial update) | Partial update design | — | — | Correct UX reasoning |
| F-1 (Test org) | Three-file structure | Own test names and cases | AI's suggested test names | Tested actual behavior, not AI's assumptions |
| F-2 (File I/O testing) | `tempfile` approach | — | `mock_open` | Tests real behavior, not mock behavior |
| G-1 (README) | Section structure | All content written from scratch | — | |
| G-2 (Docstrings) | Google-style recommendation | — | — | |

---

## 4. AI-Originated vs. Original Code Identification

The following table identifies each significant code section in the final capstone and its origin.

| File / Section | Origin | Notes |
|---|---|---|
| `book.py` — `Book` dataclass fields | **AI-originated** | Field names and default patterns came from Prompt B-1; implementation written by me |
| `book.py` — `__str__`, `__repr__` | **Original** | Structure informed by A-2 discussion; written entirely by me |
| `book.py` — `__eq__` | **Original** | Logic and normalization written by me after A-2 rationale |
| `tracked_book.py` — `TrackedBook` fields | **AI-originated** | `status` and `date_added` fields suggested in B-2 |
| `tracked_book.py` — `__str__` override | **Original** | Written by me; AI suggested ANSI colors, which I rejected |
| `tracker.py` — `BookTracker` class structure | **AI-originated** | Class name and responsibility boundary from A-1 |
| `tracker.py` — `add()`, `delete()`, `update()` | **Original** | Partially informed by E-2 for partial update logic; written by me |
| `tracker.py` — `search()` recursive function | **AI-originated (structure), Original (logic)** | Skeleton from C-1; all match logic, parameter handling, and return accumulation written by me |
| `tracker.py` — `__len__`, `__contains__` | **Original** | Placement rationale from A-2; implementation written by me |
| `tracker.py` — `save()` / `load()` | **Original** | `asdict()` approach informed by D-1; exception handling and all code written by me |
| `cli.py` — argparse skeleton | **AI-originated (structure), Original (content)** | Subparser structure from E-1; all argument names, help text, and dispatch logic written by me |
| `tests/test_book.py` | **Original** | Test organization structure from F-1; all test cases written by me |
| `tests/test_tracker.py` | **Original** | `tempfile` pattern from F-2; all test cases written by me |
| `tests/test_cli.py` | **Original** | All cases written by me |
| `README.md` | **Original** | Section structure from G-1; all content written by me |
| `docs/ADL.md` | **Original** | Written by me; no AI involvement |

**Summary:** Approximately 40% of the code has AI-originated structural elements (class names, field sets, method signatures as suggested). Approximately 60% is original — all implementation logic, control flow, error handling, test cases, and documentation content was written by me. No code block was used verbatim from AI output without modification.

---

## 5. Reflection

### What AI Accelerated

**Architecture front-loading.** The single most valuable use of AI in this capstone was at the beginning, before writing any code. Using Claude to stress-test the class hierarchy and data flow decisions before I committed to a structure saved significant refactoring time. In prior modules, I often discovered structural problems mid-implementation. Here, those problems surfaced in conversation first.

**Boilerplate pattern recall.** Python's `argparse` subcommand syntax and `dataclasses.asdict()` serialization are things I'd looked up before but couldn't reproduce from memory. AI surfaced the correct pattern in seconds, letting me focus on the domain logic rather than syntax archaeology.

**Testing strategy.** The `tempfile` vs `mock_open` discussion (Prompt F-2) was genuinely clarifying. I'd defaulted to mocking, and the AI's explanation of why `tempfile` is more meaningful for integration tests changed my approach. I learned something I'll carry forward.

**Documentation structure.** The README section scaffold (Prompt G-1) prevented the blank-page problem. Having a structure to reject or accept is faster than building one from nothing.

### What AI Distorted (or Tried To)

**Over-engineering instinct.** Claude's first architecture response included a `FileHandler` class, optional ANSI color formatting in `__str__`, and `isbn` as a field. None of these belonged in a focused CLI capstone. The AI's outputs tend toward comprehensiveness — it includes what's possible, not what's appropriate for the scope. Filtering the "could have" from the "should have" required deliberate judgment every time.

**Recursion mismatch.** The AI's initial recursion suggestions (binary search, mergesort) were technically correct but didn't fit the data model. This was the clearest case where the AI answered the literal question ("recursive function") rather than the contextual one ("recursive function that makes sense for a flat list of book objects"). I had to push back explicitly to get a useful answer.

**Generic naming.** Left to its own defaults, argparse argument names would have been `--name` and `--value`. The AI doesn't know my domain. Domain-appropriate naming is the developer's responsibility, and the AI's output is always a starting point, never a finishing point.

### What I Learned About AI-Assisted Programming

After eight weeks of using AI tools deliberately as part of coursework, a few things are clear:

**AI is best at patterns, worst at judgment.** It knows what `argparse` looks like. It doesn't know what the right argument names are for a book tracker. It knows how recursion works. It doesn't know whether recursion is the right tool for my specific data model without being pushed. The judgment layer is always mine.

**Prompting precision matters more than prompting length.** The most useful outputs came from narrow, specific prompts (Prompt C-1: "show me a skeleton — I want to write the logic myself"). The least useful came from open-ended ones early in development. Asking for a skeleton rather than a solution is a discipline worth keeping.

**The disposition step is where authorship lives.** Writing this appendix clarified something I intuited but hadn't articulated: the moment of deciding what to keep, edit, or reject is the moment of engineering judgment. The AI can generate; only I can decide whether what it generated is right for this problem. That decision process — documented here — is what separates engineering from prompting.

**AI assistance doesn't reduce the need to understand.** I couldn't have evaluated the AI's recursion suggestions without understanding recursion. I couldn't have rejected the `FileHandler` without understanding why that abstraction was unnecessary. The prerequisite for using AI well is understanding the domain well enough to know when the AI is wrong.

---

## 6. Integrity Statement

I, Waqar Javed, affirm that:

- The BookTracker CLI capstone reflects my own design and engineering judgment.
- I made every architecture decision, evaluated every AI output, and wrote all implementation logic, control flow, error handling, and tests.
- AI tools (Claude, GitHub Copilot) were used as research accelerators and drafting aids — not as the authors of the architecture or the logic.
- All AI interactions have been documented in this appendix to the best of my recollection and review.
- The AI-originated vs. original code identification in Section 4 is accurate and honest, including cases where AI-originated structure was then heavily implemented by me.
- This appendix is itself an original document. Its structure was not AI-generated, though Claude assisted with the capstone work it documents.

I understand that false statements in this appendix constitute an academic-integrity violation.

**Signed:** Waqar Javed  
**Date:** June 2025

---

*This document is part of the BookTracker CLI capstone repository. See also: `docs/ADL.md` (Architecture Decision Log), `README.md`, and the `/tests` directory.*