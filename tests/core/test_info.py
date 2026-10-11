from __future__ import annotations

from pathlib import Path

import pytest

from molkit.core.info import describe, formula
from molkit.core.model import Atom, Molecule, PuzzleModel, SourceInfo
from molkit.core.params import FDM
from molkit.core.sources.sdf import parse_sdf
from molkit.core.vec import Vec3

BENZENE_SDF = (Path(__file__).parents[1] / "fixtures" / "benzene.sdf").read_text()


PUBCHEM = SourceInfo("pubchem", "m")


def _molecule(*symbols: str, source: SourceInfo = PUBCHEM) -> Molecule:
    atoms = tuple(Atom(s, Vec3(0.0, 0.0, 0.0)) for s in symbols)
    return Molecule("m", atoms, (), source)


@pytest.mark.parametrize(
    ("symbols", "expected"),
    [
        (("C", "H", "H", "H", "H"), "CH4"),
        (("H", "C", "Cl", "Cl", "Cl"), "CHCl3"),  # Hill order: C, H, then alphabetical
        (("O", "C", "O"), "CO2"),
        (("O", "H", "H"), "H2O"),  # no carbon: everything alphabetical
        (("Na", "Cl"), "ClNa"),
    ],
)
def test_formula_uses_hill_order(symbols: tuple[str, ...], expected: str) -> None:
    assert formula(_molecule(*symbols)) == expected


def test_describe_methane(methane: Molecule) -> None:
    text = describe(PuzzleModel("id-1", methane, FDM))
    assert text.splitlines()[:3] == [
        "methane (CH4), from PubChem 'methane'",
        "5 atoms, 4 bonds: 4 single",
        "model id: id-1",
    ]
    assert "clearance_mm = 0.2" in text
    assert "include_hydrogens = True" in text


def test_describe_counts_each_bond_order() -> None:
    benzene = parse_sdf(BENZENE_SDF, SourceInfo("pubchem", "benzene"), kekulize=True)
    line = describe(PuzzleModel("id-2", benzene, FDM)).splitlines()[1]
    assert line == "12 atoms, 12 bonds: 9 single, 3 double"


def test_describe_names_cif_source() -> None:
    model = PuzzleModel("id-3", _molecule("C", source=SourceInfo("cif", "a.cif")), FDM)
    assert describe(model).splitlines()[0] == "m (C), from CIF 'a.cif'"
