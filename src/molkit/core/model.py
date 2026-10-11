"""Molecule data model: atoms (positions in Å), bonds and provenance."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from molkit.core.params import Params
from molkit.core.vec import Vec3


class BondOrder(Enum):
    """Chemical bond order; values are stable strings for serialization."""

    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    AROMATIC = "aromatic"


@dataclass(frozen=True)
class Atom:
    element: str
    position: Vec3


@dataclass(frozen=True)
class Bond:
    a: int
    b: int
    order: BondOrder


@dataclass(frozen=True)
class SourceInfo:
    """Where a molecule came from: a PubChem name or a CIF file."""

    kind: Literal["pubchem", "cif"]
    identifier: str


@dataclass(frozen=True)
class Molecule:
    name: str
    atoms: tuple[Atom, ...]
    bonds: tuple[Bond, ...]
    source: SourceInfo

    def neighbors(self, i: int) -> tuple[int, ...]:
        """Indices of the atoms bonded to atom `i`, ascending."""
        ends = [b.b for b in self.bonds if b.a == i] + [b.a for b in self.bonds if b.b == i]
        return tuple(sorted(ends))


@dataclass(frozen=True)
class PuzzleModel:
    """Everything needed to regenerate a model; this is what the Rhino anchor stores."""

    model_id: str
    molecule: Molecule
    params: Params
