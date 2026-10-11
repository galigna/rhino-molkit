from __future__ import annotations

import pytest

from molkit.core.params import FDM, RESIN, Params


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
        min_wall_mm=1.0,
    )


def test_resin_is_smaller_and_tighter_than_fdm() -> None:
    assert RESIN.scale_mm_per_a < FDM.scale_mm_per_a
    assert RESIN.clearance_mm < FDM.clearance_mm


# Guards against preset typos: the hole for the thickest peg must leave a printable wall.
@pytest.mark.parametrize("preset", [FDM, RESIN], ids=["fdm", "resin"])
def test_presets_leave_minimum_wall_around_thickest_peg(preset: Params) -> None:
    hole_radius = preset.triple_peg_radius_mm + preset.clearance_mm
    assert preset.stick_radius_mm - hole_radius >= preset.min_wall_mm
