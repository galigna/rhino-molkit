from __future__ import annotations

import dataclasses

import pytest

from molkit.core.ballstick import build
from molkit.core.model import Atom, Bond, BondOrder, Molecule, SourceInfo
from molkit.core.params import FDM
from molkit.core.vec import Vec3

GREY = (144, 144, 144)
WHITE = (255, 255, 255)
NO_H = dataclasses.replace(FDM, include_hydrogens=False)


def _approx(v: Vec3):
    return pytest.approx((v.x, v.y, v.z), abs=1e-9)


def _xyz(v: Vec3) -> tuple[float, float, float]:
    return (v.x, v.y, v.z)


def test_one_ball_per_atom_sized_from_vdw_radius(methane: Molecule) -> None:
    spec = build(methane, FDM)
    assert [b.atom_index for b in spec.balls] == [0, 1, 2, 3, 4]
    carbon, hydrogen = spec.balls[0], spec.balls[1]
    assert (carbon.element, carbon.color_rgb) == ("C", GREY)
    assert carbon.radius == pytest.approx(1.70 * 0.25 * 20.0)  # 8.5 mm
    assert (hydrogen.element, hydrogen.color_rgb) == ("H", WHITE)
    assert hydrogen.radius == pytest.approx(1.20 * 0.25 * 20.0)  # 6.0 mm


def test_ball_centres_are_scaled_from_angstrom_to_mm(methane: Molecule) -> None:
    spec = build(methane, FDM)
    assert _xyz(spec.balls[1].center) == _approx(methane.atoms[1].position * 20.0)


def test_each_bond_is_two_half_sticks_meeting_at_the_midpoint(methane: Molecule) -> None:
    sticks = build(methane, FDM).sticks
    assert len(sticks) == 2 * len(methane.bonds)
    c_half, h_half = (s for s in sticks if s.bond_index == 0)
    assert (c_half.atom_index, c_half.element, c_half.color_rgb) == (0, "C", GREY)
    assert (h_half.atom_index, h_half.element, h_half.color_rgb) == (1, "H", WHITE)
    midpoint = (methane.atoms[0].position + methane.atoms[1].position) * (0.5 * 20.0)
    assert _xyz(c_half.end) == _approx(midpoint)
    assert _xyz(h_half.end) == _approx(midpoint)
    assert _xyz(h_half.start) == _approx(methane.atoms[1].position * 20.0)
    assert {s.radius for s in sticks} == {3.5}


def test_hiding_hydrogens_drops_their_balls_and_sticks(methane: Molecule) -> None:
    spec = build(methane, NO_H)
    assert [b.atom_index for b in spec.balls] == [0]
    assert spec.sticks == ()


def test_hiding_hydrogens_keeps_original_atom_and_bond_indices() -> None:
    # Formaldehyde with hydrogens listed between the heavy atoms: H, C, H, O.
    atoms = tuple(Atom(s, Vec3(x, 0.0, 0.0)) for s, x in [("H", -1), ("C", 0), ("H", 1), ("O", 2)])
    bonds = (
        Bond(0, 1, BondOrder.SINGLE),
        Bond(1, 2, BondOrder.SINGLE),
        Bond(1, 3, BondOrder.DOUBLE),
    )
    spec = build(Molecule("formaldehyde", atoms, bonds, SourceInfo("pubchem", "x")), NO_H)
    assert [b.atom_index for b in spec.balls] == [1, 3]
    assert [(s.bond_index, s.atom_index) for s in spec.sticks] == [(2, 1), (2, 3)]
