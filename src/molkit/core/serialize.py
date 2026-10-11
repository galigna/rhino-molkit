"""PuzzleModel <-> JSON, for storage on the Rhino anchor object."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from molkit.core.errors import ModelDataError
from molkit.core.model import Atom, Bond, BondOrder, Molecule, PuzzleModel, SourceInfo
from molkit.core.params import Params
from molkit.core.vec import Vec3

SCHEMA_VERSION = 1


def dumps(model: PuzzleModel) -> str:
    """Serialize a model to JSON."""
    data = {"schema_version": SCHEMA_VERSION, **asdict(model)}
    return json.dumps(data, default=lambda enum: enum.value)  # BondOrder is the only non-JSON type


def loads(text: str) -> PuzzleModel:
    """Rebuild a model from `dumps` output; stored data may be edited, so failures are wrapped."""
    try:
        data = json.loads(text)
        version = data["schema_version"]
        if version != SCHEMA_VERSION:
            raise ModelDataError(f"unsupported model data version {version}")
        return PuzzleModel(data["model_id"], _molecule(data["molecule"]), Params(**data["params"]))
    except (ValueError, KeyError, TypeError) as error:
        raise ModelDataError(f"corrupt model data: {error!r}") from None


def _molecule(data: dict[str, Any]) -> Molecule:
    return Molecule(
        data["name"],
        tuple(Atom(a["element"], Vec3(**a["position"])) for a in data["atoms"]),
        tuple(Bond(b["a"], b["b"], BondOrder(b["order"])) for b in data["bonds"]),
        SourceInfo(**data["source"]),
    )
