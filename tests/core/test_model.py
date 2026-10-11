from __future__ import annotations

import dataclasses
import math

import pytest

from molkit.core.errors import AtomIndexError, UnknownElementError, ValidationError
from molkit.core.model import Atom, Bond, BondOrder, Molecule, SourceInfo
from molkit.core.vec import Vec3

ORIGIN = Vec3(0.0, 0.0, 0.0)
SOURCE = SourceInfo("pubchem", "test")


def _atom(symbol: str, x: float = 0.0) -> Atom:
    return Atom(symbol, Vec3(x, 0.0, 0.0))


# --- Atom -------------------------------------------------------------------


def test_atom_defaults_to_neutral() -> None:
    assert Atom("C", ORIGIN).formal_charge == 0


def test_atom_rejects_non_canonical_symbol() -> None:
    with pytest.raises(ValidationError, match="'Cl'"):
        Atom("CL", ORIGIN)


def test_atom_rejects_unknown_element() -> None:
    with pytest.raises(UnknownElementError):
        Atom("Xx", ORIGIN)


def test_atom_is_hydrogen() -> None:
    assert Atom("H", ORIGIN).is_hydrogen
    assert not Atom("C", ORIGIN).is_hydrogen


# --- Bond -------------------------------------------------------------------


@pytest.mark.parametrize(("a", "b"), [(1, 1), (2, 1), (-1, 3)])
def test_bond_requires_ordered_non_negative_indices(a: int, b: int) -> None:
    with pytest.raises(ValidationError):
        Bond(a, b, BondOrder.SINGLE)


def test_bond_between_sorts_indices() -> None:
    assert Bond.between(4, 2, BondOrder.DOUBLE) == Bond(2, 4, BondOrder.DOUBLE)


def test_bond_other_returns_partner() -> None:
    bond = Bond(2, 5, BondOrder.SINGLE)
    assert bond.other(2) == 5
    assert bond.other(5) == 2


def test_bond_other_rejects_atom_not_in_bond() -> None:
    with pytest.raises(AtomIndexError):
        Bond(2, 5, BondOrder.SINGLE).other(3)


def test_bond_involves() -> None:
    bond = Bond(2, 5, BondOrder.SINGLE)
    assert bond.involves(2)
    assert bond.involves(5)
    assert not bond.involves(3)


# --- SourceInfo -------------------------------------------------------------


def test_source_info_rejects_unknown_kind() -> None:
    with pytest.raises(ValidationError, match="kind"):
        SourceInfo("pdb", "1abc")  # type: ignore[arg-type]


@pytest.mark.parametrize("identifier", ["", "   "])
def test_source_info_rejects_blank_identifier(identifier: str) -> None:
    with pytest.raises(ValidationError):
        SourceInfo("cif", identifier)


# --- Molecule: validation ---------------------------------------------------


def test_methane_has_reference_geometry(methane: Molecule) -> None:
    carbon = methane.atoms[0].position
    hydrogens = [atom.position - carbon for atom in methane.atoms[1:]]
    assert [h.norm() for h in hydrogens] == pytest.approx([1.09] * 4)
    angle = math.degrees(hydrogens[0].angle_to(hydrogens[1]))
    assert angle == pytest.approx(109.47, abs=0.01)


@pytest.mark.parametrize("name", ["", "  "])
def test_molecule_rejects_blank_name(methane: Molecule, name: str) -> None:
    with pytest.raises(ValidationError, match="name"):
        dataclasses.replace(methane, name=name)


def test_molecule_rejects_empty_atoms(methane: Molecule) -> None:
    with pytest.raises(ValidationError, match="at least one atom"):
        dataclasses.replace(methane, atoms=(), bonds=())


def test_molecule_rejects_bond_to_missing_atom(methane: Molecule) -> None:
    bonds = (*methane.bonds, Bond(0, 5, BondOrder.SINGLE))
    with pytest.raises(ValidationError, match="out of range"):
        dataclasses.replace(methane, bonds=bonds)


def test_molecule_rejects_duplicate_bonds(methane: Molecule) -> None:
    bonds = (*methane.bonds, Bond(0, 1, BondOrder.DOUBLE))
    with pytest.raises(ValidationError, match="duplicate"):
        dataclasses.replace(methane, bonds=bonds)


# --- Molecule: neighbors ----------------------------------------------------


def test_neighbors_of_carbon(methane: Molecule) -> None:
    assert methane.neighbors(0) == (1, 2, 3, 4)


def test_neighbors_of_hydrogen(methane: Molecule) -> None:
    assert methane.neighbors(3) == (0,)


@pytest.mark.parametrize("index", [5, -1])
def test_neighbors_rejects_bad_index(methane: Molecule, index: int) -> None:
    with pytest.raises(AtomIndexError):
        methane.neighbors(index)


# --- Molecule: without_hydrogens --------------------------------------------


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


def test_without_hydrogens_keeps_molecule_without_hydrogens() -> None:
    co2 = Molecule(
        "carbon dioxide",
        (_atom("O", -1.16), _atom("C"), _atom("O", 1.16)),
        (Bond(0, 1, BondOrder.DOUBLE), Bond(1, 2, BondOrder.DOUBLE)),
        SOURCE,
    )
    assert co2.without_hydrogens() == co2


def test_without_hydrogens_on_all_hydrogen_molecule_raises() -> None:
    h2 = Molecule(
        "hydrogen", (_atom("H"), _atom("H", 0.74)), (Bond(0, 1, BondOrder.SINGLE),), SOURCE
    )
    with pytest.raises(ValidationError, match="at least one atom"):
        h2.without_hydrogens()


def test_molecule_is_immutable(methane: Molecule) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        methane.name = "ethane"  # type: ignore[misc]
