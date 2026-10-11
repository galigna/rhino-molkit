from __future__ import annotations

import dataclasses

import pytest

from molkit.core.elements import Element, all_elements, element
from molkit.core.errors import UnknownElementError, ValidationError

CARBON = element("C")


def test_lookup_returns_carbon_data() -> None:
    assert CARBON == Element("C", 6, 12.011, 0.76, 1.70, (144, 144, 144))


@pytest.mark.parametrize("symbol", ["Cl", "cl", "CL", " Cl "])
def test_lookup_normalizes_symbol(symbol: str) -> None:
    assert element(symbol).symbol == "Cl"


@pytest.mark.parametrize("symbol", ["Xx", "", "Carbon"])
def test_lookup_unknown_symbol_raises(symbol: str) -> None:
    with pytest.raises(UnknownElementError, match="unknown element"):
        element(symbol)


def test_table_covers_organic_elements() -> None:
    symbols = {e.symbol for e in all_elements()}
    assert {"H", "C", "N", "O", "F", "P", "S", "Cl", "Br", "I"} <= symbols


def test_table_is_sorted_by_atomic_number_without_duplicates() -> None:
    numbers = [e.atomic_number for e in all_elements()]
    assert numbers == sorted(set(numbers))


def test_mass_increases_with_atomic_number() -> None:
    masses = [e.mass for e in all_elements()]
    assert masses == sorted(masses)


def test_vdw_radius_exceeds_covalent_radius() -> None:
    assert all(e.vdw_radius > e.covalent_radius for e in all_elements())


@pytest.mark.parametrize(
    "changes",
    [
        {"symbol": ""},
        {"symbol": "c"},
        {"symbol": "CL"},
        {"atomic_number": 0},
        {"mass": 0.0},
        {"covalent_radius": -0.1},
        {"vdw_radius": 0.0},
        {"color_rgb": (256, 0, 0)},
        {"color_rgb": (0, -1, 0)},
    ],
)
def test_invalid_element_data_is_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        dataclasses.replace(CARBON, **changes)
