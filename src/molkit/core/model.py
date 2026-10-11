"""Molecule data model: atoms (positions in Å), bonds and provenance."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Literal, get_args

from molkit.core.elements import element
from molkit.core.errors import AtomIndexError, ValidationError
from molkit.core.vec import Vec3

SourceKind = Literal["pubchem", "cif"]


class BondOrder(Enum):
    """Chemical bond order; values are stable strings for serialization."""

    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    AROMATIC = "aromatic"


@dataclass(frozen=True)
class Atom:
    """One atom. `element` must be a canonical symbol such as "Cl"."""

    element: str
    position: Vec3
    formal_charge: int = 0

    def __post_init__(self) -> None:
        canonical = element(self.element).symbol
        if canonical != self.element:
            raise ValidationError(f"use canonical symbol {canonical!r}, not {self.element!r}")

    @property
    def is_hydrogen(self) -> bool:
        """True for hydrogen atoms."""
        return self.element == "H"


@dataclass(frozen=True)
class Bond:
    """A bond between atom indices `a < b`."""

    a: int
    b: int
    order: BondOrder

    def __post_init__(self) -> None:
        if not 0 <= self.a < self.b:
            raise ValidationError(f"bond needs 0 <= a < b, got ({self.a}, {self.b})")

    @classmethod
    def between(cls, i: int, j: int, order: BondOrder) -> Bond:
        """Build a bond from two indices in either order."""
        return cls(min(i, j), max(i, j), order)

    def involves(self, i: int) -> bool:
        """True if atom `i` is one of the bond's ends."""
        return i in (self.a, self.b)

    def other(self, i: int) -> int:
        """The index at the opposite end from atom `i`."""
        if not self.involves(i):
            raise AtomIndexError(f"atom {i} is not in bond ({self.a}, {self.b})")
        return self.b if i == self.a else self.a


@dataclass(frozen=True)
class SourceInfo:
    """Where a molecule came from: a PubChem name or a CIF file."""

    kind: SourceKind
    identifier: str

    def __post_init__(self) -> None:
        if self.kind not in get_args(SourceKind):
            raise ValidationError(f"unknown source kind: {self.kind!r}")
        if not self.identifier.strip():
            raise ValidationError("source identifier must not be blank")


@dataclass(frozen=True)
class Molecule:
    """A named molecule: atoms, the bonds between them, and its source."""

    name: str
    atoms: tuple[Atom, ...]
    bonds: tuple[Bond, ...]
    source: SourceInfo

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("molecule name must not be blank")
        if not self.atoms:
            raise ValidationError("a molecule needs at least one atom")
        self._check_bonds()

    def neighbors(self, i: int) -> tuple[int, ...]:
        """Indices of the atoms bonded to atom `i`, ascending."""
        if not 0 <= i < len(self.atoms):
            raise AtomIndexError(f"atom index {i} out of range ({len(self.atoms)} atoms)")
        return tuple(sorted(bond.other(i) for bond in self.bonds if bond.involves(i)))

    def without_hydrogens(self) -> Molecule:
        """A copy with hydrogens and their bonds removed, atoms renumbered in order."""
        keep = [i for i, atom in enumerate(self.atoms) if not atom.is_hydrogen]
        new_index = {old: new for new, old in enumerate(keep)}
        bonds = tuple(
            Bond(new_index[bond.a], new_index[bond.b], bond.order)
            for bond in self.bonds
            if bond.a in new_index and bond.b in new_index
        )
        return replace(self, atoms=tuple(self.atoms[i] for i in keep), bonds=bonds)

    def _check_bonds(self) -> None:
        pairs = [(bond.a, bond.b) for bond in self.bonds]
        if any(b >= len(self.atoms) for _, b in pairs):
            raise ValidationError(f"bond atom index out of range ({len(self.atoms)} atoms)")
        if len(set(pairs)) != len(pairs):
            raise ValidationError("duplicate bond between the same two atoms")
