"""Element table: masses, radii and display colours.

Sources:
- mass: IUPAC conventional standard atomic weights (u)
- covalent_radius: Cordero et al., Dalton Trans. 2008 (Å; C is sp3)
- vdw_radius: Bondi, J. Phys. Chem. 1964; Mantina et al., J. Phys. Chem. A 2009
  where Bondi gives no value (B, Al, Ca) (Å). Metals Bondi doesn't cover (Fe, Co, Mn, Cr, ...)
  are left out rather than guessed.
- color_rgb: Jmol CPK colours
"""

from __future__ import annotations

from dataclasses import dataclass

from molkit.core.errors import UnknownElementError


@dataclass(frozen=True)
class Element:
    symbol: str
    atomic_number: int
    mass: float
    covalent_radius: float
    vdw_radius: float
    color_rgb: tuple[int, int, int]


ELEMENTS: dict[str, Element] = {
    e.symbol: e
    for e in (
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
        Element("Ni", 28, 58.693, 1.24, 1.63, (80, 208, 80)),
        Element("Cu", 29, 63.546, 1.32, 1.40, (200, 128, 51)),
        Element("Zn", 30, 65.38, 1.22, 1.39, (125, 128, 176)),
        Element("Ga", 31, 69.723, 1.22, 1.87, (194, 143, 143)),
        Element("As", 33, 74.922, 1.19, 1.85, (189, 128, 227)),
        Element("Se", 34, 78.971, 1.20, 1.90, (255, 161, 0)),
        Element("Br", 35, 79.904, 1.20, 1.85, (166, 41, 41)),
        Element("Pd", 46, 106.42, 1.39, 1.63, (0, 105, 133)),
        Element("Ag", 47, 107.87, 1.45, 1.72, (192, 192, 192)),
        Element("Cd", 48, 112.41, 1.44, 1.58, (255, 217, 143)),
        Element("Sn", 50, 118.71, 1.39, 2.17, (102, 128, 128)),
        Element("I", 53, 126.904, 1.39, 1.98, (148, 0, 148)),
        Element("Pt", 78, 195.08, 1.36, 1.72, (208, 208, 224)),
        Element("Au", 79, 196.97, 1.36, 1.66, (255, 209, 35)),
        Element("Hg", 80, 200.59, 1.32, 1.55, (184, 184, 208)),
        Element("Pb", 82, 207.2, 1.46, 2.02, (87, 89, 97)),
    )
}


def element(symbol: str) -> Element:
    """Look up an element by its canonical symbol, e.g. "Cl"."""
    try:
        return ELEMENTS[symbol]
    except KeyError:
        raise UnknownElementError(f"unknown element symbol: {symbol!r}") from None
