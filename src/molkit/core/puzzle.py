"""Molecule + Params -> puzzle pieces (one per atom) and printability checks. Lengths in mm.

Each piece is a ball with half-bonds; neighbours join at the bond midpoint, peg into hole.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

from molkit.core.ballstick import ball_radius, visible_atoms
from molkit.core.elements import element
from molkit.core.model import Bond, BondOrder, Molecule
from molkit.core.params import Params
from molkit.core.vec import Vec3


class Gender(Enum):
    PEG = "peg"
    HOLE = "hole"


class ProfileKind(Enum):
    ROUND = "round"
    D_FLAT = "d_flat"  # one flat: fits one way
    DOUBLE_FLAT = "double_flat"  # two parallel flats: fits two ways


# Rotation-honest: single bonds spin, double bonds lock planar, aromatic rings lock with
# two-fold symmetry, triple bonds are linear so rotation is irrelevant.
_PROFILE_KINDS = {
    BondOrder.SINGLE: ProfileKind.ROUND,
    BondOrder.DOUBLE: ProfileKind.D_FLAT,
    BondOrder.AROMATIC: ProfileKind.DOUBLE_FLAT,
    BondOrder.TRIPLE: ProfileKind.ROUND,
}

# Below this sine, a neighbour is treated as collinear with the bond.
_MIN_SINE = 0.1

# Crush ribs: three, 120° apart so they centre the peg; measured from the key_ref, so they sit
# in the same place on every hole. On a flat they push in from the flat.
_RIB_ANGLES = tuple(math.radians(a) for a in (90.0, 210.0, 330.0))
_RIB_WIDTH_MM = 0.8  # at the hole wall; two 0.4 mm extrusion lines


@dataclass(frozen=True)
class PegProfile:
    """Cross-section of a peg or hole. `flat_depth` is cut in from `radius` (unused if ROUND)."""

    kind: ProfileKind
    radius: float
    flat_depth: float
    rib_height: float = 0.0  # crush ribs reaching in from the wall; holes only


@dataclass(frozen=True)
class Joint:
    bond_index: int
    partner_index: int
    direction: Vec3  # unit, piece centre -> partner
    key_ref: Vec3  # unit, perpendicular to direction: the flats' normal; same on both halves
    length: float  # piece centre -> bond midpoint, where the stub ends
    gender: Gender
    profile: PegProfile  # holes are already enlarged by the clearance and carry the ribs
    depth: float  # peg length beyond the midpoint, or hole depth inward from it
    chamfer: float  # peg tip lead-in; 0 for holes


@dataclass(frozen=True)
class PieceSpec:
    atom_index: int
    element: str
    center: Vec3
    ball_radius: float
    stick_radius: float
    color_rgb: tuple[int, int, int]
    joints: tuple[Joint, ...]


@dataclass(frozen=True)
class Issue:
    atom_index: int
    message: str


def build_pieces(molecule: Molecule, params: Params) -> tuple[PieceSpec, ...]:
    """One piece per visible atom. Atom and bond indices always refer to `molecule`."""
    shown = visible_atoms(molecule, params)
    bonds = [(i, b) for i, b in enumerate(molecule.bonds) if b.a in shown and b.b in shown]
    key_refs = {i: _key_ref(molecule, b) for i, b in bonds}  # once per bond: halves must agree
    return tuple(
        _piece(molecule, atom, [(i, b) for i, b in bonds if atom in (b.a, b.b)], key_refs, params)
        for atom in shown
    )


def check(pieces: tuple[PieceSpec, ...], params: Params) -> tuple[Issue, ...]:
    """Everything that would make the pieces unprintable or impossible to assemble."""
    per_piece = (issue for piece in pieces for issue in _piece_issues(piece, params))
    return tuple(itertools.chain(per_piece, _overlaps(pieces)))


def outline(profile: PegProfile, segments: int = 128) -> tuple[tuple[float, float], ...]:
    """Cross-section polygon in the joint plane, whose +x axis is the key_ref.

    Samples the circle and clamps x onto the flats: points past a flat land on its chord,
    which gives the exact D or double-flat shape. Points on a rib move in by the rib height.
    128 segments deviate < 0.001 mm at r = 2 mm and put about 8 points on each rib.
    """
    flat_x = profile.radius - profile.flat_depth
    low, high = _FLAT_LIMITS[profile.kind](flat_x, profile.radius)
    angles = (2 * math.pi * k / segments for k in range(segments))
    return tuple(
        _rib_inset(
            profile,
            a,
            min(max(profile.radius * math.cos(a), low), high),
            profile.radius * math.sin(a),
        )
        for a in angles
    )


def _rib_inset(profile: PegProfile, angle: float, x: float, y: float) -> tuple[float, float]:
    half_width = _RIB_WIDTH_MM / 2 / profile.radius  # radians
    on_rib = any(
        abs((angle - rib + math.pi) % (2 * math.pi) - math.pi) <= half_width for rib in _RIB_ANGLES
    )
    if not on_rib:
        return x, y
    scale = 1 - profile.rib_height / math.hypot(x, y)
    return x * scale, y * scale


_FLAT_LIMITS = {
    ProfileKind.ROUND: lambda flat_x, r: (-r, r),
    ProfileKind.D_FLAT: lambda flat_x, r: (-r, flat_x),
    ProfileKind.DOUBLE_FLAT: lambda flat_x, r: (-flat_x, flat_x),
}


def _piece(
    molecule: Molecule,
    atom: int,
    bonds: list[tuple[int, Bond]],
    key_refs: dict[int, Vec3],
    params: Params,
) -> PieceSpec:
    symbol = molecule.atoms[atom].element
    return PieceSpec(
        atom_index=atom,
        element=symbol,
        center=molecule.atoms[atom].position * params.scale_mm_per_a,
        ball_radius=ball_radius(symbol, params),
        stick_radius=params.stick_radius_mm,
        color_rgb=element(symbol).color_rgb,
        joints=tuple(_joint(molecule, i, b, atom, key_refs[i], params) for i, b in bonds),
    )


def _joint(
    molecule: Molecule, bond_index: int, bond: Bond, atom: int, key_ref: Vec3, params: Params
) -> Joint:
    partner = bond.b if atom == bond.a else bond.a
    offset = molecule.atoms[partner].position - molecule.atoms[atom].position
    is_peg = atom != _hole_atom(molecule, bond)
    return Joint(
        bond_index=bond_index,
        partner_index=partner,
        direction=offset.unit(),
        key_ref=key_ref,
        length=offset.norm() * params.scale_mm_per_a / 2,
        gender=Gender.PEG if is_peg else Gender.HOLE,
        profile=_profile(bond.order, is_peg, params),
        depth=params.peg_length_mm + (0.0 if is_peg else params.hole_extra_depth_mm),
        chamfer=params.chamfer_mm if is_peg else 0.0,
    )


def _hole_atom(molecule: Molecule, bond: Bond) -> int:
    """The heavier element gets the hole, so light ends (H, halogens) carry pegs.
    Equal masses: the lower index gets the hole."""
    return max((bond.a, bond.b), key=lambda i: (element(molecule.atoms[i].element).mass, -i))


def _profile(order: BondOrder, is_peg: bool, params: Params) -> PegProfile:
    radius = params.triple_peg_radius_mm if order is BondOrder.TRIPLE else params.peg_radius_mm
    # The hole is the peg offset outward by the clearance; its flats move out by the same
    # amount, so the flat depth (measured from the radius) is unchanged.
    clearance, ribs = (0.0, 0.0) if is_peg else (params.clearance_mm, params.rib_height_mm)
    return PegProfile(_PROFILE_KINDS[order], radius + clearance, params.flat_depth_mm, ribs)


def _key_ref(molecule: Molecule, bond: Bond) -> Vec3:
    """Normal of the plane through the bond and a neighbour: the pi-orbital direction.
    Falls back to a fixed perpendicular when every neighbour is collinear (or there are none)."""
    axis = (molecule.atoms[bond.b].position - molecule.atoms[bond.a].position).unit()
    for center, other in ((bond.a, bond.b), (bond.b, bond.a)):
        for neighbour in molecule.neighbors(center):
            side = molecule.atoms[neighbour].position - molecule.atoms[center].position
            normal = axis.cross(side.unit())
            if neighbour != other and normal.norm() > _MIN_SINE:
                return normal.unit()
    helper = Vec3(1.0, 0.0, 0.0) if abs(axis.x) < 0.9 else Vec3(0.0, 1.0, 0.0)
    return axis.cross(helper).unit()


def _piece_issues(piece: PieceSpec, params: Params) -> Iterator[Issue]:
    label = f"{piece.element}{piece.atom_index}"
    for j in piece.joints:
        where = f"{label}: joint to atom {j.partner_index}"
        if j.length <= piece.ball_radius:
            yield Issue(piece.atom_index, f"{where} is inside the ball")
        if j.gender is Gender.HOLE:
            wall = piece.stick_radius - j.profile.radius
            if wall < params.min_wall_mm:
                yield Issue(piece.atom_index, f"{where}: wall {wall:.2f} mm < {params.min_wall_mm}")
            if j.depth >= j.length:
                yield Issue(piece.atom_index, f"{where}: hole reaches past the ball centre")


def _overlaps(pieces: tuple[PieceSpec, ...]) -> Iterator[Issue]:
    for p, q in itertools.combinations(pieces, 2):
        if (q.center - p.center).norm() < p.ball_radius + q.ball_radius:
            names = f"{p.element}{p.atom_index} and {q.element}{q.atom_index}"
            yield Issue(p.atom_index, f"{names}: balls overlap")
