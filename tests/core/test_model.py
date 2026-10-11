from __future__ import annotations

import math

import pytest

from molkit.core.model import Atom, Bond, BondOrder, Molecule, SourceInfo
from molkit.core.vec import Vec3

SOURCE = SourceInfo("pubchem", "test")


def _atom(symbol: str, x: float = 0.0) -> Atom:
    return Atom(symbol, Vec3(x, 0.0, 0.0))


def test_methane_has_reference_geometry(methane: Molecule) -> None:
    carbon = methane.atoms[0].position
    h1, h2 = (atom.position - carbon for atom in methane.atoms[1:3])
    assert h1.norm() == pytest.approx(1.09)
    cos_hch = h1.unit().dot(h2.unit())
    assert math.degrees(math.acos(cos_hch)) == pytest.approx(109.47, abs=0.01)


def test_neighbors_of_carbon(methane: Molecule) -> None:
    assert methane.neighbors(0) == (1, 2, 3, 4)


def test_neighbors_of_hydrogen(methane: Molecule) -> None:
    assert methane.neighbors(3) == (0,)


def test_neighbors_sees_bonds_from_either_end() -> None:
    chain = Molecule(
        "chain",
        (_atom("C"), _atom("C", 1.5), _atom("C", 3.0)),
        (Bond(2, 1, BondOrder.SINGLE), Bond(0, 1, BondOrder.SINGLE)),
        SOURCE,
    )
    assert chain.neighbors(1) == (0, 2)


def test_without_hydrogens_on_methane_leaves_lone_carbon(methane: Molecule) -> None:
    heavy = methane.without_hydrogens()
    assert heavy.atoms == (methane.atoms[0],)
    assert heavy.bonds == ()
    assert (heavy.name, heavy.source) == (methane.name, methane.source)


def test_without_hydrogens_reindexes_atoms_and_bonds() -> None:
    # Formaldehyde with hydrogens listed between the heavy atoms: H, C, H, O.
    atoms = (_atom("H", -1.0), _atom("C"), _atom("H", 1.0), _atom("O", 2.0))
    bonds = (
        Bond(0, 1, BondOrder.SINGLE),
        Bond(1, 2, BondOrder.SINGLE),
        Bond(1, 3, BondOrder.DOUBLE),
    )
    heavy = Molecule("formaldehyde", atoms, bonds, SOURCE).without_hydrogens()
    assert heavy.atoms == (atoms[1], atoms[3])
    assert heavy.bonds == (Bond(0, 1, BondOrder.DOUBLE),)
