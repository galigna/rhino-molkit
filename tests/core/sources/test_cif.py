from __future__ import annotations

import math
from collections import Counter
from pathlib import Path

import pytest

from molkit.core.errors import CifParseError, NoMoleculeFoundError, UnknownElementError
from molkit.core.info import formula
from molkit.core.model import BondOrder, Molecule, SourceInfo
from molkit.core.sources import cif
from molkit.core.sources.cif import parse_cif

FIXTURES = Path(__file__).parents[2] / "fixtures"
ASPIRIN = "aspirin_cod2104857.cif"


def _parse(file: str, kekulize: bool = False) -> tuple[Molecule, tuple[str, ...]]:
    return parse_cif((FIXTURES / file).read_text(), SourceInfo("cif", file), kekulize)


def _lengths(molecule: Molecule) -> list[float]:
    return [
        (molecule.atoms[b.a].position - molecule.atoms[b.b].position).norm() for b in molecule.bonds
    ]


def _orders(molecule: Molecule) -> Counter[BondOrder]:
    return Counter(b.order for b in molecule.bonds)


# --- a real structure: aspirin, P2_1/c, four molecules per cell (COD 2104857) ------


def test_aspirin_gives_one_whole_molecule() -> None:
    aspirin, notes = _parse(ASPIRIN)
    assert formula(aspirin) == "C9H8O4"
    assert len(aspirin.bonds) == 21
    # X-ray H positions sit on the bonding electron density: O-H refines to 0.82 A, not 0.97.
    assert all(0.8 < length < 1.6 for length in _lengths(aspirin))
    assert notes == ()


def test_aspirin_bond_orders_are_perceived() -> None:
    aspirin, _ = _parse(ASPIRIN)
    # benzene ring, plus C=O in the acid and in the ester
    assert _orders(aspirin) == {BondOrder.AROMATIC: 6, BondOrder.DOUBLE: 2, BondOrder.SINGLE: 13}


def test_aspirin_kekulized() -> None:
    aspirin, _ = _parse(ASPIRIN, kekulize=True)
    assert _orders(aspirin) == {BondOrder.DOUBLE: 5, BondOrder.SINGLE: 16}


def test_name_is_the_file_name_without_extension() -> None:
    aspirin, _ = _parse(ASPIRIN)
    assert aspirin.name == "aspirin_cod2104857"
    assert aspirin.source == SourceInfo("cif", ASPIRIN)


# --- hand-made edge cases ------------------------------------------------------------


def test_molecule_split_across_the_cell_edge_comes_out_whole() -> None:
    methane, _ = _parse("methane_split.cif")
    assert formula(methane) == "CH4"
    assert _lengths(methane) == pytest.approx([1.09] * 4, abs=0.01)


def test_only_the_first_disorder_alternative_is_kept() -> None:
    methane, _ = _parse("methane_disorder.cif")
    assert formula(methane) == "CH4"
    c = methane.atoms[0].position
    h1, h2 = (a.position - c for a in methane.atoms[1:3])
    assert math.degrees(math.acos(h1.unit().dot(h2.unit()))) == pytest.approx(109.47, abs=0.1)


def test_missing_hydrogens_are_noted() -> None:
    co2, notes = _parse("co2.cif")
    assert _orders(co2) == {BondOrder.DOUBLE: 2}
    assert notes == ("the file has no hydrogen positions, so the model has none",)


def test_polymer_is_not_a_molecule() -> None:
    with pytest.raises(NoMoleculeFoundError, match="polymer"):
        _parse("carbon_chain.cif")


def test_element_outside_the_table_raises() -> None:
    with pytest.raises(UnknownElementError, match="Fe"):
        _parse("iron.cif")


def test_failed_bond_order_perception_falls_back_to_single_bonds(monkeypatch) -> None:
    def fail(mol, charge):
        raise ValueError("cannot assign")

    monkeypatch.setattr(cif.rdDetermineBonds, "DetermineBondOrders", fail)
    aspirin, notes = _parse(ASPIRIN)
    assert _orders(aspirin) == {BondOrder.SINGLE: 21}
    assert notes == ("bond orders could not be determined, so every bond is single",)


@pytest.mark.parametrize(
    "text",
    ["this is not a CIF", "data_empty\n_cell_length_a 10\n"],
    ids=["garbage", "no-atom-sites"],
)
def test_unreadable_cif_raises(text: str) -> None:
    with pytest.raises(CifParseError, match=r"broken.cif"):
        parse_cif(text, SourceInfo("cif", "broken.cif"))
