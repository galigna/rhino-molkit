from __future__ import annotations

import dataclasses
import re

import pytest

from molkit.core.params import FDM, PRESETS, RESIN, Params, option_name, with_preset


def test_fdm_preset_matches_spec_table() -> None:
    assert FDM == Params(
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
        ridge_height_mm=0.3,
        min_wall_mm=1.0,
    )


def test_resin_is_smaller_and_tighter_than_fdm() -> None:
    assert RESIN.scale_mm_per_a < FDM.scale_mm_per_a
    assert RESIN.clearance_mm < FDM.clearance_mm


# Guards against preset typos: the hole for the thickest peg must leave a printable wall.
@pytest.mark.parametrize("preset", [FDM, RESIN], ids=["fdm", "resin"])
def test_presets_leave_minimum_wall_around_thickest_peg(preset: Params) -> None:
    groove_radius = preset.triple_peg_radius_mm + preset.ridge_height_mm
    hole_radius = max(preset.triple_peg_radius_mm + preset.clearance_mm, groove_radius)
    assert preset.stick_radius_mm - hole_radius >= preset.min_wall_mm


def test_presets_are_listed_by_display_name() -> None:
    assert PRESETS == {"FDM": FDM, "Resin": RESIN}


def test_applying_a_preset_takes_printer_values_but_keeps_hydrogen_choice() -> None:
    mine = dataclasses.replace(FDM, include_hydrogens=False, clearance_mm=0.3)
    assert with_preset(mine, RESIN) == dataclasses.replace(RESIN, include_hydrogens=False)


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("clearance_mm", "Clearance"),
        ("scale_mm_per_a", "Scale"),
        ("triple_peg_radius_mm", "TriplePegRadius"),
        ("include_hydrogens", "IncludeHydrogens"),
        ("ball_radius_factor", "BallRadiusFactor"),
    ],
)
def test_option_name_is_camel_case_without_mm_suffix(field: str, expected: str) -> None:
    assert option_name(field) == expected


def test_every_param_gets_a_distinct_valid_rhino_option_name() -> None:
    names = [option_name(f.name) for f in dataclasses.fields(Params)]
    assert len(set(names)) == len(names)
    assert all(re.fullmatch(r"[A-Z][A-Za-z0-9]*", n) for n in names)  # Rhino's option-name rule
