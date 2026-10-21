"""Model and puzzle parameters, with FDM and resin presets."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Params:
    scale_mm_per_a: float
    ball_radius_factor: float  # times the element's vdW radius
    stick_radius_mm: float
    include_hydrogens: bool
    peg_radius_mm: float
    triple_peg_radius_mm: float  # thicker, so a triple bond is visibly different from a single
    flat_depth_mm: float  # how far the key flat cuts in from the peg radius
    peg_length_mm: float
    hole_extra_depth_mm: float  # room at the bottom of the hole so the peg seats fully
    clearance_mm: float  # radial gap between peg and hole
    chamfer_mm: float  # peg lead-in
    rib_height_mm: float  # crush ribs inside each hole; they squash a little around the peg
    min_wall_mm: float


# Starting points; tune after the first test prints (SPEC M9).
FDM = Params(
    scale_mm_per_a=20.0,
    ball_radius_factor=0.25,
    stick_radius_mm=3.5,
    include_hydrogens=True,
    peg_radius_mm=1.75,
    triple_peg_radius_mm=2.1,
    flat_depth_mm=0.6,
    peg_length_mm=5.0,
    hole_extra_depth_mm=0.4,
    clearance_mm=0.2,
    chamfer_mm=0.3,
    rib_height_mm=0.3,  # ribs reach 0.1 mm into the peg: snug, and they hold when worn
    min_wall_mm=1.0,  # about 2.5 perimeters with a 0.4 mm nozzle
)

RESIN = Params(
    scale_mm_per_a=12.0,
    ball_radius_factor=0.25,
    stick_radius_mm=2.2,
    include_hydrogens=True,
    peg_radius_mm=1.1,
    triple_peg_radius_mm=1.35,
    flat_depth_mm=0.4,
    peg_length_mm=3.5,
    hole_extra_depth_mm=0.3,
    clearance_mm=0.1,
    chamfer_mm=0.2,
    rib_height_mm=0.15,
    min_wall_mm=0.6,
)

PRESETS: dict[str, Params] = {"FDM": FDM, "Resin": RESIN}


def with_preset(params: Params, preset: Params) -> Params:
    """Preset values, except hydrogens: that is a choice about the molecule, not the printer."""
    return replace(preset, include_hydrogens=params.include_hydrogens)


_UNIT_SUFFIXES = ("_mm_per_a", "_mm")  # longest first


def option_name(field_name: str) -> str:
    """Rhino command-line option name for a Params field, e.g. clearance_mm -> Clearance."""
    for suffix in _UNIT_SUFFIXES:
        field_name = field_name.removesuffix(suffix)
    return "".join(word.capitalize() for word in field_name.split("_"))
