"""STL file names and the JSON assembly manifest written next to them."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from typing import Any

from molkit.core.info import formula
from molkit.core.model import PuzzleModel
from molkit.core.puzzle import Joint, PieceSpec


def safe_name(name: str) -> str:
    """`name` with anything a file name can't safely hold replaced by underscores."""
    return re.sub(r"[^\w-]+", "_", name)


def piece_filename(model_name: str, piece: PieceSpec) -> str:
    return f"{safe_name(model_name)}_{piece.atom_index:03}_{piece.element}.stl"


def manifest_json(model: PuzzleModel, pieces: tuple[PieceSpec, ...]) -> str:
    """Which file is which atom, and which pieces join to which: the assembly instructions."""
    m = model.molecule
    data = {
        "molecule": m.name,
        "formula": formula(m),
        "source": asdict(m.source),
        "model_id": model.model_id,
        "params": asdict(model.params),
        "pieces": [
            {
                "file": piece_filename(m.name, p),
                "atom_index": p.atom_index,
                "element": p.element,
                "joints": [_joint(model, j) for j in p.joints],
            }
            for p in pieces
        ],
    }
    return json.dumps(data, indent=2)


def _joint(model: PuzzleModel, joint: Joint) -> dict[str, Any]:
    return {
        "partner": joint.partner_index,
        "partner_element": model.molecule.atoms[joint.partner_index].element,
        "bond": model.molecule.bonds[joint.bond_index].order.value,
        "gender": joint.gender.value,
        "shape": joint.profile.kind.value,
    }
