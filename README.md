# molkit

A Rhino 8 plugin that turns molecules into 3D-printable puzzles: one piece per atom, joined by
pegs whose shape encodes the bond order.

> **Status: early development.** PubChem and CIF models, puzzle pieces and STL export work. Peg
> and clearance sizes haven't been test-printed yet, and packaging (Yak) is next. See [SPEC.md](SPEC.md) for the plan.

## What works now

| Command | Does |
|---|---|
| `MolkitFetch` | Fetches a compound from PubChem by name and builds a ball-and-stick model. PubChem only has 3D structures for molecules up to 50 heavy atoms; for larger ones RDKit generates the coordinates. Option `Kekulize` shows aromatic rings as alternating single/double bonds. |
| `MolkitImportCif` | Opens a CIF file of a molecular crystal, applies the crystal symmetry and builds one whole molecule, even if the file cuts it at the cell edge. Polymers and frameworks are rejected. |
| `MolkitInfo` | Click any part of a model to print its formula, bonds, source and parameters. |
| `MolkitSettings` | Edit a model's parameters (scale, hydrogens, peg sizes, clearance, …) or apply the FDM/Resin preset, then rebuild it. |
| `MolkitPuzzle` | Split a model into printable pieces, one per atom: pegs shaped by bond order, holes with clearance. Problems (thin walls, overlapping balls, …) are listed instead of building broken pieces. |
| `MolkitExportStl` | Write one STL per piece (in mm) plus a `<name>_manifest.json` that says which piece joins which. |
| `MolkitRegenerate` | Rebuild a model from its stored data, e.g. after deleting parts by hand. |

Models are rebuilt from data stored on the model (a locked anchor point), not edited by hand.

## Try it in Rhino 8

Until the Yak package exists, follow the one-time setup in
[docs/smoke-test.md](docs/smoke-test.md): put a `molkit-dev.pth` file pointing at `src` into
Rhino's Python `site-packages`, then run `_-RunPythonScript "<repo>\rhino\commands\MolkitFetch.py"`.

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
