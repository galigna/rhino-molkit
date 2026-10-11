from __future__ import annotations

import json

from molkit.core.manifest import manifest_json, piece_filename, safe_name
from molkit.core.model import Molecule, PuzzleModel
from molkit.core.params import FDM
from molkit.core.puzzle import build_pieces


def test_safe_name_replaces_characters_files_cannot_hold() -> None:
    assert safe_name("acetic acid/2:x") == "acetic_acid_2_x"
    assert safe_name("2,4-D") == "2_4-D"


def test_piece_filename_has_name_index_and_element(methane: Molecule) -> None:
    carbon = build_pieces(methane, FDM)[0]
    assert piece_filename("methane", carbon) == "methane_000_C.stl"


def test_manifest_lists_every_piece_with_its_joints(methane: Molecule) -> None:
    model = PuzzleModel("id-1", methane, FDM)
    data = json.loads(manifest_json(model, build_pieces(methane, FDM)))
    assert (data["molecule"], data["formula"], data["model_id"]) == ("methane", "CH4", "id-1")
    assert data["params"]["clearance_mm"] == 0.2
    assert [p["file"] for p in data["pieces"]] == [
        "methane_000_C.stl",
        "methane_001_H.stl",
        "methane_002_H.stl",
        "methane_003_H.stl",
        "methane_004_H.stl",
    ]
    carbon, hydrogen = data["pieces"][0], data["pieces"][1]
    assert carbon["joints"][0] == {
        "partner": 1,
        "partner_element": "H",
        "bond": "single",
        "gender": "hole",
        "shape": "round",
    }
    assert hydrogen["joints"] == [
        {"partner": 0, "partner_element": "C", "bond": "single", "gender": "peg", "shape": "round"}
    ]
