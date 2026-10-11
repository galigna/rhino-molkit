"""Molecule + Params -> ball-and-stick geometry spec (mm)."""

from __future__ import annotations

from dataclasses import dataclass

from molkit.core.elements import element
from molkit.core.model import Molecule
from molkit.core.params import Params
from molkit.core.vec import Vec3


@dataclass(frozen=True)
class BallSpec:
    atom_index: int
    element: str
    center: Vec3
    radius: float
    color_rgb: tuple[int, int, int]


@dataclass(frozen=True)
class StickSpec:
    """Half of a bond: from an atom's centre to the bond midpoint, in that atom's colour."""

    atom_index: int
    bond_index: int
    element: str
    start: Vec3
    end: Vec3
    radius: float
    color_rgb: tuple[int, int, int]


@dataclass(frozen=True)
class BallStickSpec:
    balls: tuple[BallSpec, ...]
    sticks: tuple[StickSpec, ...]


def build(molecule: Molecule, params: Params) -> BallStickSpec:
    """Lay out balls and half-sticks. Atom and bond indices always refer to `molecule`."""
    shown = visible_atoms(molecule, params)
    balls = tuple(_ball(molecule, i, params) for i in shown)
    sticks = tuple(
        _half_stick(molecule, bond_index, atom_index, params)
        for bond_index, bond in enumerate(molecule.bonds)
        if bond.a in shown and bond.b in shown
        for atom_index in (bond.a, bond.b)
    )
    return BallStickSpec(balls, sticks)


def visible_atoms(molecule: Molecule, params: Params) -> list[int]:
    """Indices of the atoms to build; hydrogens are skipped when params hide them."""
    return [
        i
        for i, atom in enumerate(molecule.atoms)
        if params.include_hydrogens or atom.element != "H"
    ]


def ball_radius(symbol: str, params: Params) -> float:
    """Ball radius in mm: a fraction of the van der Waals radius, scaled."""
    return element(symbol).vdw_radius * params.ball_radius_factor * params.scale_mm_per_a


def _ball(molecule: Molecule, i: int, params: Params) -> BallSpec:
    atom = molecule.atoms[i]
    center = atom.position * params.scale_mm_per_a
    radius = ball_radius(atom.element, params)
    return BallSpec(i, atom.element, center, radius, element(atom.element).color_rgb)


def _half_stick(molecule: Molecule, bond_index: int, atom_index: int, params: Params) -> StickSpec:
    bond = molecule.bonds[bond_index]
    a, b = molecule.atoms[bond.a].position, molecule.atoms[bond.b].position
    midpoint = (a + b) * (0.5 * params.scale_mm_per_a)
    atom = molecule.atoms[atom_index]
    start = atom.position * params.scale_mm_per_a
    color = element(atom.element).color_rgb
    return StickSpec(
        atom_index, bond_index, atom.element, start, midpoint, params.stick_radius_mm, color
    )
