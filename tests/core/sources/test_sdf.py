from __future__ import annotations

import math
from collections import Counter
from pathlib import Path

import pytest
from rdkit import Chem

from molkit.core.errors import No3DConformerError, SdfParseError, UnknownElementError
from molkit.core.model import BondOrder, Molecule, SourceInfo
from molkit.core.sources.sdf import parse_sdf

FIXTURES = Path(__file__).parents[2] / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / f"{name}.sdf").read_text()


def _parse(name: str, kekulize: bool = False) -> Molecule:
    return parse_sdf(_read(name), SourceInfo("pubchem", name), kekulize)


def _cc_orders(molecule: Molecule) -> Counter[BondOrder]:
    return Counter(
        b.order
        for b in molecule.bonds
        if molecule.atoms[b.a].element == molecule.atoms[b.b].element == "C"
    )


def test_methane_keeps_explicit_hydrogens() -> None:
    methane = _parse("methane")
    assert [a.element for a in methane.atoms] == ["C", "H", "H", "H", "H"]
    assert [b.order for b in methane.bonds] == [BondOrder.SINGLE] * 4
    assert methane.neighbors(0) == (1, 2, 3, 4)


def test_methane_has_tetrahedral_geometry() -> None:
    methane = _parse("methane")
    c = methane.atoms[0].position
    h1, h2 = (a.position - c for a in methane.atoms[1:3])
    assert h1.norm() == pytest.approx(1.09, abs=0.01)
    angle = math.degrees(math.acos(h1.unit().dot(h2.unit())))
    assert angle == pytest.approx(109.5, abs=1.0)


def test_name_and_source_come_from_source_info() -> None:
    methane = _parse("methane")
    assert methane.name == "methane"
    assert methane.source == SourceInfo("pubchem", "methane")


def test_benzene_ring_is_aromatic_by_default() -> None:
    benzene = _parse("benzene")
    assert len(benzene.atoms) == 12
    assert _cc_orders(benzene) == {BondOrder.AROMATIC: 6}


def test_benzene_kekulized_alternates_single_and_double() -> None:
    benzene = _parse("benzene", kekulize=True)
    assert _cc_orders(benzene) == {BondOrder.SINGLE: 3, BondOrder.DOUBLE: 3}


def test_unparseable_text_raises() -> None:
    with pytest.raises(SdfParseError, match="broken"):
        parse_sdf("not a molfile", SourceInfo("pubchem", "broken"))


def test_2d_record_raises() -> None:
    flat = Chem.MolToMolBlock(Chem.MolFromSmiles("C"))
    with pytest.raises(No3DConformerError):
        parse_sdf(flat, SourceInfo("pubchem", "methane"))


def test_element_outside_table_raises() -> None:
    iron = _read("methane").replace(" C   0", " Fe  0", 1)
    with pytest.raises(UnknownElementError, match="Fe"):
        parse_sdf(iron, SourceInfo("pubchem", "iron"))


@pytest.mark.parametrize("code", ["8", "9"])  # V2000 "any" and dative bonds
def test_bond_type_without_peg_shape_raises(code: str) -> None:
    odd = _read("methane").replace("  1  2  1  0", f"  1  2  {code}  0", 1)
    with pytest.raises(SdfParseError, match="bond type"):
        parse_sdf(odd, SourceInfo("pubchem", "methane"))
