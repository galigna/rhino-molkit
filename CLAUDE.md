# CLAUDE.md — molkit

Rhino 8 plugin that generates 3D-printable molecular puzzles. **SPEC.md is the source of truth**
for scope, data model, defaults, and milestone order. Read it before starting any milestone, and
update it when a decision changes.

## Architecture rules (non-negotiable)

- `src/molkit/core/` is **pure Python**. It never imports `Rhino`, `rhinoscriptsyntax`,
  `scriptcontext`, `System`, `clr`, or `Grasshopper`, not even inside functions or under
  `TYPE_CHECKING`. `tests/test_architecture.py` enforces this.
- `src/molkit/rhino/` is a **thin adapter**. It turns core specs into Rhino objects and handles user
  input. It makes no chemistry or puzzle decisions. If you need an `if` about atoms, bonds, or
  geometry rules there, move that logic into core.
- `rhino/commands/*.py` entry scripts only call a function in `molkit.rhino.commands`.
- Molecule data and parameters live on the model's anchor object (`molkit.model` user dictionary
  key). Geometry is always **regenerated** from that data and is never patched in place.
- `rdkit` and `gemmi` are allowed in core. Network access goes only through `core/sources/pubchem.py`
  with an injectable HTTP function.

## Python and style

- Target **Python 3.9** (Rhino 8's CPython).
  - Start every module with `from __future__ import annotations`.
  - No `match`, no `X | Y` outside annotations, no `dataclass(slots=True)`, no
    `str.removeprefix`-era assumptions without checking that they exist in 3.9.
- **Type hints on everything**: parameters, return values, and module constants. Core must pass
  `mypy --strict` (`ignore_missing_imports` only for rdkit/gemmi).
- **Frozen dataclasses** for all data: `@dataclass(frozen=True)`, with `tuple` instead of `list`
  and no mutable defaults. Use `dataclasses.replace` to make modified copies.
- **Short functions**: aim for ≤ 20 lines and one job each.
- **No duplication**: element data, presets, and constants are defined once. Search before
  writing a helper.
- Pure functions in core: no global state, no I/O except in `sources/` and `stl.py`'s byte output,
  no `print` (use `logging`).
- Errors subclass `MolkitError` (`core/errors.py`). Never raise a bare `Exception`.
- Units: Å in `Molecule`, mm in every spec. Put the unit in the name when it isn't obvious
  (`clearance_mm`).
- Docstrings: one line for each public function, and more only when the *why* isn't obvious.
- Format and lint with **ruff** (`ruff format`, `ruff check`). Config is in `pyproject.toml`.

## Testing

- **Every public core function has pytest tests.** Core coverage is 100% (line and branch), and CI
  fails below that.
- Tests mirror the source layout: `tests/core/<pkg>/test_<module>.py`.
- No network in tests. Use fixture files in `tests/fixtures/` and fake HTTP transports.
- Geometry assertions use `pytest.approx` with an explicit tolerance.
- Write the test first or alongside the code, never "later".
- The Rhino adapter is checked with the manual checklist in `docs/smoke-test.md`. Add a line for
  each new command or behaviour.

## Commands

```bash
ruff format . && ruff check .
mypy src/molkit/core
pytest --cov=molkit.core --cov-branch --cov-fail-under=100
```

## Workflow

- Work **one milestone at a time** in SPEC.md order. Don't start the next one until the current one
  meets its definition of done.
- **Commit after each milestone** (and at sensible points within one) using Conventional Commits,
  e.g. `feat(core): add bond gender rule (M8)`. Never commit with failing checks.
- Keep the README current with every user-visible change.
- Prove each slice on **methane** first (the reference molecule). Bring in other molecules only to
  cover features methane can't, such as other bond orders and rings.
- Don't add dependencies, files, or features outside the current milestone without asking.
- If a spec decision turns out to be wrong in practice (for example, test-print results), propose
  the change to SPEC.md before coding around it.

## Code style: lazy senior
- The best code is no code. Before writing anything, check if RDKit, gemmi,
  RhinoCommon, or the Python standard library already does it.
- Write the simplest thing that works for the current milestone. No speculative
  features, no "might need later" parameters, no abstractions until there are
  3 real uses.
- Prefer data over logic: lookup tables (dicts, enums) instead of if/elif chains.
- Functions do one thing and fit on one screen. No classes where a function
  plus a dataclass will do.
- No defensive clutter: validate only at boundaries (user input, files, network),
  trust internal code.
- No comments that restate the code. Comment only the "why" (chemistry facts,
  tolerances, Rhino quirks).
- Readability beats cleverness: short means fewer concepts, not dense one-liners.
- Deleting code is a win. When changing something, remove what it replaces.