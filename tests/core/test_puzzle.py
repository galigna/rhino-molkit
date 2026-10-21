from __future__ import annotations

import dataclasses
import math
from pathlib import Path

import pytest

from molkit.core.model import Atom, BondOrder, Molecule, SourceInfo
from molkit.core.params import FDM
from molkit.core.puzzle import (
    Gender,
    Joint,
    PegProfile,
    PieceSpec,
    ProfileKind,
    build_pieces,
    check,
    outline,
)
from molkit.core.sources.sdf import parse_sdf
from molkit.core.vec import Vec3

FIXTURES = Path(__file__).parents[1] / "fixtures"


def _load(name: str) -> Molecule:
    return parse_sdf((FIXTURES / f"{name}.sdf").read_text(), SourceInfo("pubchem", name))


def _joint(pieces: tuple[PieceSpec, ...], atom: int, partner: int) -> Joint:
    return next(j for j in pieces[atom].joints if j.partner_index == partner)


def _carbon_carbon_bond(molecule: Molecule) -> tuple[int, int]:
    return next(
        (b.a, b.b)
        for b in molecule.bonds
        if molecule.atoms[b.a].element == molecule.atoms[b.b].element == "C"
    )


# --- pieces -------------------------------------------------------------------------


def test_one_piece_per_atom_with_one_joint_per_bond(methane: Molecule) -> None:
    pieces = build_pieces(methane, FDM)
    assert [p.atom_index for p in pieces] == [0, 1, 2, 3, 4]
    assert [len(p.joints) for p in pieces] == [4, 1, 1, 1, 1]
    carbon = pieces[0]
    assert (carbon.element, carbon.color_rgb) == ("C", (144, 144, 144))
    assert carbon.ball_radius == pytest.approx(8.5)
    assert carbon.stick_radius == 3.5


def test_joint_points_at_partner_and_ends_at_bond_midpoint(methane: Molecule) -> None:
    joint = _joint(build_pieces(methane, FDM), 0, 1)
    to_h = methane.atoms[1].position - methane.atoms[0].position
    assert joint.direction.dot(to_h.unit()) == pytest.approx(1.0)
    assert joint.length == pytest.approx(to_h.norm() * 20.0 / 2)


def test_hiding_hydrogens_keeps_indices_and_drops_their_joints(methane: Molecule) -> None:
    pieces = build_pieces(methane, dataclasses.replace(FDM, include_hydrogens=False))
    assert [(p.atom_index, p.joints) for p in pieces] == [(0, ())]


# --- gender: the heavier atom gets the hole ----------------------------------------


def test_heavier_atom_gets_the_hole(methane: Molecule) -> None:
    pieces = build_pieces(methane, FDM)
    assert {j.gender for j in pieces[0].joints} == {Gender.HOLE}
    assert [p.joints[0].gender for p in pieces[1:]] == [Gender.PEG] * 4


def test_equal_masses_give_the_hole_to_the_lower_index() -> None:
    ethylene = _load("ethylene")
    a, b = _carbon_carbon_bond(ethylene)
    pieces = build_pieces(ethylene, FDM)
    assert _joint(pieces, min(a, b), max(a, b)).gender is Gender.HOLE
    assert _joint(pieces, max(a, b), min(a, b)).gender is Gender.PEG


def test_peg_and_hole_depths_and_chamfer(methane: Molecule) -> None:
    pieces = build_pieces(methane, FDM)
    hole, peg = _joint(pieces, 0, 1), _joint(pieces, 1, 0)
    assert (peg.depth, peg.chamfer) == (5.0, 0.3)
    assert (hole.depth, hole.chamfer) == (pytest.approx(5.4), 0.0)


def test_peg_sections_run_shaft_ridge_shaft_then_chamfered_tip(methane: Molecule) -> None:
    peg = _joint(build_pieces(methane, FDM), 1, 0)
    radii = [round(p.radius, 6) for p, _ in peg.sections]
    zs = [z for _, z in peg.sections]
    assert radii == [1.75, 1.75, 2.05, 2.05, 1.75, 1.75, 1.45]  # ridge 0.3, tip -0.3
    assert zs == pytest.approx([0.0, 3.0, 3.3, 3.7, 4.0, 4.7, 5.0], abs=0.01)
    assert zs == sorted(zs)


def test_hole_groove_sits_where_the_ridge_lands_and_matches_its_size(methane: Molecule) -> None:
    pieces = build_pieces(methane, FDM)
    hole, peg = _joint(pieces, 0, 1), _joint(pieces, 1, 0)
    groove = [(p.radius, -z) for p, z in hole.sections[:5]]
    ridge = [(p.radius, z) for p, z in peg.sections[:5]]
    assert [z for _, z in groove] == pytest.approx([z for _, z in ridge])
    assert max(r for r, _ in groove) == pytest.approx(2.05)  # = ridge, 0.1 mm wider than the bore
    assert hole.sections[-1][1] == pytest.approx(-5.4)
    assert {round(p.radius, 6) for p, _ in hole.sections} == {1.95, 2.05}


# --- profiles: shape encodes bond order -------------------------------------------


@pytest.mark.parametrize(
    ("name", "kind", "peg_radius"),
    [
        ("methane", ProfileKind.ROUND, 1.75),  # single: spins freely
        ("ethylene", ProfileKind.D_FLAT, 1.75),  # double: locked, fits one way
        ("benzene", ProfileKind.DOUBLE_FLAT, 1.75),  # aromatic: locked, fits two ways
        ("acetylene", ProfileKind.ROUND, 2.1),  # triple: round but thicker
    ],
)
def test_profile_follows_bond_order(name: str, kind: ProfileKind, peg_radius: float) -> None:
    molecule = _load(name)
    a, b = _carbon_carbon_bond(molecule) if name != "methane" else (0, 1)
    pieces = build_pieces(molecule, FDM)
    hole, peg = _joint(pieces, min(a, b), max(a, b)), _joint(pieces, max(a, b), min(a, b))
    assert peg.profile.kind is hole.profile.kind is kind
    assert peg.profile.radius == pytest.approx(peg_radius)
    assert hole.profile.radius == pytest.approx(peg_radius + 0.2)  # clearance
    assert hole.profile.flat_depth == peg.profile.flat_depth == 0.6


def test_benzene_ring_bonds_are_aromatic() -> None:
    benzene = _load("benzene")
    assert {b.order for b in benzene.bonds} == {BondOrder.SINGLE, BondOrder.AROMATIC}


# --- key reference: orientation of the flats ----------------------------------------


def test_key_ref_is_unit_perpendicular_and_shared_by_both_halves() -> None:
    ethylene = _load("ethylene")
    a, b = _carbon_carbon_bond(ethylene)
    pieces = build_pieces(ethylene, FDM)
    hole, peg = _joint(pieces, min(a, b), max(a, b)), _joint(pieces, max(a, b), min(a, b))
    assert hole.key_ref == peg.key_ref
    assert hole.key_ref.norm() == pytest.approx(1.0)
    assert hole.key_ref.dot(hole.direction) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("name", ["ethylene", "benzene"])
def test_key_ref_is_normal_to_planar_molecule(name: str) -> None:
    # The pi orbital, and so the flat's normal, is perpendicular to the molecular plane.
    molecule = _load(name)
    a, b = _carbon_carbon_bond(molecule)
    key = _joint(build_pieces(molecule, FDM), a, b).key_ref
    origin = molecule.atoms[a].position
    for atom in molecule.atoms:
        assert key.dot(atom.position - origin) == pytest.approx(0.0, abs=0.01)


def test_linear_molecule_still_gets_a_valid_key_ref() -> None:
    acetylene = _load("acetylene")  # every neighbour is collinear with the bond
    for piece in build_pieces(acetylene, FDM):
        for joint in piece.joints:
            assert joint.key_ref.norm() == pytest.approx(1.0)
            assert joint.key_ref.dot(joint.direction) == pytest.approx(0.0, abs=1e-9)


# --- printability checks -----------------------------------------------------------


@pytest.mark.parametrize("name", ["methane", "ethylene", "acetylene", "benzene"])
def test_defaults_are_printable(name: str) -> None:
    assert check(build_pieces(_load(name), FDM), FDM) == ()


def test_thin_wall_around_hole_is_reported(methane: Molecule) -> None:
    params = dataclasses.replace(FDM, stick_radius_mm=2.5)  # groove: 2.5 - 2.05 = 0.45 < 1.0
    issues = check(build_pieces(methane, params), params)
    assert len(issues) == 4  # one per C-H hole
    assert all("wall" in i.message and i.atom_index == 0 for i in issues)


def test_wall_is_measured_at_the_groove(methane: Molecule) -> None:
    params = dataclasses.replace(FDM, ridge_height_mm=1.0)  # groove 2.75: wall 0.75 < 1.0
    issues = check(build_pieces(methane, params), params)
    assert len(issues) == 4
    assert all("wall" in i.message for i in issues)


def test_joint_inside_ball_is_reported(methane: Molecule) -> None:
    params = dataclasses.replace(FDM, ball_radius_factor=0.4)  # C ball 13.6 mm > 10.9 mm
    issues = check(build_pieces(methane, params), params)
    assert any("inside" in i.message and i.atom_index == 0 for i in issues)


def test_hole_past_ball_centre_is_reported(methane: Molecule) -> None:
    params = dataclasses.replace(FDM, peg_length_mm=11.0)  # hole 11.4 mm > 10.9 mm
    issues = check(build_pieces(methane, params), params)
    assert any("centre" in i.message and i.atom_index == 0 for i in issues)


def test_overlapping_balls_are_reported() -> None:
    near = tuple(Atom("C", Vec3(x, 0.0, 0.0)) for x in (0.0, 0.5))  # not bonded, 10 mm apart
    pieces = build_pieces(Molecule("pair", near, (), SourceInfo("pubchem", "x")), FDM)
    (issue,) = check(pieces, FDM)
    assert "overlap" in issue.message
    assert issue.atom_index == 0


# --- outline: cross-section polygon for the Rhino adapter --------------------------


def _xs(profile: PegProfile) -> list[float]:
    return [x for x, _ in outline(profile)]


def test_round_outline_is_a_circle() -> None:
    points = outline(PegProfile(ProfileKind.ROUND, 2.0, 0.6))
    assert len(points) == 64
    assert all(math.hypot(x, y) == pytest.approx(2.0) for x, y in points)


def test_d_flat_outline_is_cut_on_the_positive_x_side_only() -> None:
    xs = _xs(PegProfile(ProfileKind.D_FLAT, 2.0, 0.6))
    assert max(xs) == pytest.approx(1.4)  # flat at radius - flat_depth
    assert min(xs) == pytest.approx(-2.0)


def test_double_flat_outline_is_cut_on_both_sides() -> None:
    xs = _xs(PegProfile(ProfileKind.DOUBLE_FLAT, 2.0, 0.6))
    assert (min(xs), max(xs)) == (pytest.approx(-1.4), pytest.approx(1.4))


def test_outline_points_stay_inside_the_circle() -> None:
    points = outline(PegProfile(ProfileKind.DOUBLE_FLAT, 2.0, 0.6))
    assert all(math.hypot(x, y) <= 2.0 + 1e-9 for x, y in points)
