# molkit

A Rhino 8 plugin that turns molecules into 3D-printable puzzles: one piece per atom, joined by
pegs whose shape encodes the bond order.

> **Status: early development.** Ball-and-stick models from PubChem work; puzzle pieces, CIF
> import and STL export are coming. See [SPEC.md](SPEC.md) for the plan.

## What works now

| Command | Does |
|---|---|
| `MolkitFetch` | Fetches a compound from PubChem by name and builds a ball-and-stick model. Option `Kekulize` shows aromatic rings as alternating single/double bonds. |
| `MolkitInfo` | Click any part of a model to print its formula, bonds, source and parameters. |

Models are rebuilt from data stored on the model (a locked anchor point), not edited by hand.

## Try it in Rhino 8

Until the Yak package exists, follow the one-time setup in
[docs/smoke-test.md](docs/smoke-test.md): add `src` to the Script Editor's Python 3 module search
paths, then run `_-RunPythonScript "<repo>\rhino\commands\MolkitFetch.py"`.

The first run installs RDKit and gemmi into Rhino's Python (about 40 MB). Rhino's installer times
out after 15 s, so on a slow connection the first attempt may fail. Run it again.

## Development

Core logic lives in `src/molkit/core/` (pure Python, no Rhino imports, 100% test coverage). The
Rhino adapter in `src/molkit/rhino/` only draws what core computes.

```bash
uv sync
uv run pytest --cov=molkit.core
uv run ruff check . && uv run mypy
```

Requires [uv](https://docs.astral.sh/uv/). Everything runs on Python 3.9, the version Rhino 8
embeds. Coding rules are in [CLAUDE.md](CLAUDE.md).
