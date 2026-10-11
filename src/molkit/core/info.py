"""Human-readable summaries of a model (for MolkitInfo)."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict

from molkit.core.model import BondOrder, Molecule, PuzzleModel

_SOURCE_LABELS = {"pubchem": "PubChem", "cif": "CIF"}


def formula(molecule: Molecule) -> str:
    """Formula in Hill order: C, H, then alphabetical (all alphabetical if there is no C)."""
    counts = Counter(atom.element for atom in molecule.atoms)
    first = ["C", "H"] if "C" in counts else []
    order = [s for s in first if s in counts] + sorted(s for s in counts if s not in first)
    return "".join(s + (str(counts[s]) if counts[s] > 1 else "") for s in order)


def describe(model: PuzzleModel) -> str:
    """Multi-line summary: name, formula, source, bond orders, model id and parameters."""
    m = model.molecule
    orders = Counter(bond.order for bond in m.bonds)
    bond_counts = ", ".join(f"{orders[o]} {o.value}" for o in BondOrder if orders[o])
    lines = [
        f"{m.name} ({formula(m)}), from {_SOURCE_LABELS[m.source.kind]} {m.source.identifier!r}",
        f"{len(m.atoms)} atoms, {len(m.bonds)} bonds: {bond_counts}",
        f"model id: {model.model_id}",
        *(f"  {name} = {value}" for name, value in asdict(model.params).items()),
    ]
    return "\n".join(lines)
