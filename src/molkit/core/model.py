"""Molecule data model: atoms (positions in Å), bonds and provenance."""

from __future__ import annotations

from dataclasses import dataclass, replace
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

    def without_hydrogens(self) -> Molecule:
        """A copy with hydrogens and their bonds removed, atoms renumbered in order."""
        keep = [i for i, atom in enumerate(self.atoms) if atom.element != "H"]
        new_index = {old: new for new, old in enumerate(keep)}
        bonds = tuple(
            Bond(new_index[b.a], new_index[b.b], b.order)
            for b in self.bonds
            if b.a in new_index and b.b in new_index
        )
        return replace(self, atoms=tuple(self.atoms[i] for i in keep), bonds=bonds)


@dataclass(frozen=True)
class PuzzleModel:
    """Everything needed to regenerate a model; this is what the Rhino anchor stores."""

    model_id: str
    molecule: Molecule
    params: Params
