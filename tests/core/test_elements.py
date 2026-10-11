from __future__ import annotations

import pytest

from molkit.core.elements import ELEMENTS, Element, element
from molkit.core.errors import UnknownElementError


def test_lookup_returns_carbon_data() -> None:
    assert element("C") == Element("C", 6, 12.011, 0.76, 1.70, (144, 144, 144))


def test_lookup_returns_copper_data() -> None:
    assert element("Cu") == Element("Cu", 29, 63.546, 1.32, 1.40, (200, 128, 51))


@pytest.mark.parametrize("symbol", ["Ni", "Zn", "Pd", "Ag", "Pt", "Au", "Hg"])
def test_table_covers_common_metals(symbol: str) -> None:
    assert element(symbol).symbol == symbol


@pytest.mark.parametrize("symbol", ["Xx", "CL", ""])
def test_lookup_unknown_symbol_raises(symbol: str) -> None:
    with pytest.raises(UnknownElementError, match="unknown element"):
        element(symbol)


def test_table_covers_organic_elements() -> None:
    assert {"H", "C", "N", "O", "F", "P", "S", "Cl", "Br", "I"} <= ELEMENTS.keys()


# The table has no runtime validation, so these sanity checks guard against typos.


def test_mass_increases_with_atomic_number() -> None:
    by_number = sorted(ELEMENTS.values(), key=lambda e: e.atomic_number)
    masses = [e.mass for e in by_number]
    assert masses == sorted(masses)


def test_vdw_radius_exceeds_covalent_radius() -> None:
    assert all(e.vdw_radius > e.covalent_radius for e in ELEMENTS.values())


def test_colours_are_valid_rgb() -> None:
    assert all(0 <= c <= 255 for e in ELEMENTS.values() for c in e.color_rgb)
