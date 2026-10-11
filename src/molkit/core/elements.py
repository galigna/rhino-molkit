"""Element table: masses, radii and display colours.

Sources:
- mass: IUPAC conventional standard atomic weights (u)
- covalent_radius: Cordero et al., Dalton Trans. 2008 (Å; C is sp3)
- vdw_radius: Bondi, J. Phys. Chem. 1964; Mantina et al., J. Phys. Chem. A 2009
  where Bondi gives no value (B, Al, Ca) (Å)
- color_rgb: Jmol CPK colours
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from molkit.core.errors import UnknownElementError, ValidationError


@dataclass(frozen=True)
class Element:
    """Static properties of one chemical element."""

    symbol: str
    atomic_number: int
    mass: float
    covalent_radius: float
    vdw_radius: float
    color_rgb: tuple[int, int, int]

    def __post_init__(self) -> None:
        if not self.symbol or self.symbol != self.symbol.capitalize():
            raise ValidationError(f"element symbol must be capitalized, got {self.symbol!r}")
        if self.atomic_number < 1:
            raise ValidationError(f"atomic number must be >= 1, got {self.atomic_number}")
        _require_positive(
            self.symbol,
            mass=self.mass,
            covalent_radius=self.covalent_radius,
            vdw_radius=self.vdw_radius,
        )
        if not all(0 <= c <= 255 for c in self.color_rgb):
            raise ValidationError(f"{self.symbol}: colour components must be 0-255")


def _require_positive(symbol: str, **values: float) -> None:
    for name, value in values.items():
        if value <= 0:
            raise ValidationError(f"{symbol}: {name} must be > 0, got {value}")


_ELEMENTS: tuple[Element, ...] = (
    Element("H", 1, 1.008, 0.31, 1.20, (255, 255, 255)),
    Element("Li", 3, 6.94, 1.28, 1.82, (204, 128, 255)),
    Element("B", 5, 10.81, 0.84, 1.92, (255, 181, 181)),
    Element("C", 6, 12.011, 0.76, 1.70, (144, 144, 144)),
    Element("N", 7, 14.007, 0.71, 1.55, (48, 80, 248)),
    Element("O", 8, 15.999, 0.66, 1.52, (255, 13, 13)),
    Element("F", 9, 18.998, 0.57, 1.47, (144, 224, 80)),
    Element("Na", 11, 22.990, 1.66, 2.27, (171, 92, 242)),
    Element("Mg", 12, 24.305, 1.41, 1.73, (138, 255, 0)),
    Element("Al", 13, 26.982, 1.21, 1.84, (191, 166, 166)),
    Element("Si", 14, 28.085, 1.11, 2.10, (240, 200, 160)),
    Element("P", 15, 30.974, 1.07, 1.80, (255, 128, 0)),
    Element("S", 16, 32.06, 1.05, 1.80, (255, 255, 48)),
    Element("Cl", 17, 35.45, 1.02, 1.75, (31, 240, 31)),
    Element("K", 19, 39.098, 2.03, 2.75, (143, 64, 212)),
    Element("Ca", 20, 40.078, 1.76, 2.31, (61, 255, 0)),
    Element("Se", 34, 78.971, 1.20, 1.90, (255, 161, 0)),
    Element("Br", 35, 79.904, 1.20, 1.85, (166, 41, 41)),
    Element("I", 53, 126.904, 1.39, 1.98, (148, 0, 148)),
)

_BY_SYMBOL: Mapping[str, Element] = MappingProxyType({e.symbol: e for e in _ELEMENTS})


def element(symbol: str) -> Element:
    """Look up an element by symbol, ignoring case and surrounding spaces ("CL" -> Cl)."""
    try:
        return _BY_SYMBOL[symbol.strip().capitalize()]
    except KeyError:
        raise UnknownElementError(f"unknown element symbol: {symbol!r}") from None


def all_elements() -> tuple[Element, ...]:
    """Every supported element, ordered by atomic number."""
    return _ELEMENTS
