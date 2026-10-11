from __future__ import annotations

import math

import pytest

from molkit.core.model import Atom, Bond, BondOrder, Molecule, SourceInfo
from molkit.core.vec import Vec3

CH_BOND_A = 1.09


def _tetrahedral_h(sign_x: int, sign_y: int, sign_z: int) -> Atom:
    k = CH_BOND_A / math.sqrt(3)
    return Atom("H", Vec3(sign_x * k, sign_y * k, sign_z * k))


@pytest.fixture
def methane() -> Molecule:
    """Reference molecule: C at the origin, four H at tetrahedral corners."""
    atoms = (
        Atom("C", Vec3(0.0, 0.0, 0.0)),
        _tetrahedral_h(1, 1, 1),
        _tetrahedral_h(1, -1, -1),
        _tetrahedral_h(-1, 1, -1),
        _tetrahedral_h(-1, -1, 1),
    )
    bonds = tuple(Bond(0, h, BondOrder.SINGLE) for h in range(1, 5))
    return Molecule("methane", atoms, bonds, SourceInfo("pubchem", "methane"))
