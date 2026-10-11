from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from molkit.core.errors import ModelDataError
from molkit.core.model import Molecule, PuzzleModel, SourceInfo
from molkit.core.params import FDM, RESIN
from molkit.core.serialize import dumps, loads
from molkit.core.sources.sdf import parse_sdf

BENZENE_SDF = (Path(__file__).parents[1] / "fixtures" / "benzene.sdf").read_text()


def test_methane_model_round_trips(methane: Molecule) -> None:
    model = PuzzleModel("id-1", methane, FDM)
    assert loads(dumps(model)) == model


def test_bond_orders_and_custom_params_round_trip() -> None:
    benzene = parse_sdf(BENZENE_SDF, SourceInfo("pubchem", "benzene"))
    model = PuzzleModel("id-2", benzene, dataclasses.replace(RESIN, clearance_mm=0.15))
    assert loads(dumps(model)) == model


def test_json_records_schema_version(methane: Molecule) -> None:
    assert json.loads(dumps(PuzzleModel("id-1", methane, FDM)))["schema_version"] == 1


def test_unknown_schema_version_raises(methane: Molecule) -> None:
    data = json.loads(dumps(PuzzleModel("id-1", methane, FDM)))
    data["schema_version"] = 99
    with pytest.raises(ModelDataError, match="version 99"):
        loads(json.dumps(data))


@pytest.mark.parametrize(
    "text",
    ["not json", "{}", '{"schema_version": 1, "model_id": "x"}', "[1, 2]"],
)
def test_corrupt_data_raises(text: str) -> None:
    with pytest.raises(ModelDataError):
        loads(text)


def test_models_saved_before_generated_3d_existed_still_load(methane: Molecule) -> None:
    data = json.loads(dumps(PuzzleModel("id-1", methane, FDM)))
    del data["molecule"]["source"]["generated_3d"]
    assert loads(json.dumps(data)).molecule.source == SourceInfo("pubchem", "methane")


def test_generated_3d_flag_round_trips(methane: Molecule) -> None:
    source = SourceInfo("pubchem", "methane", generated_3d=True)
    model = PuzzleModel("id-1", dataclasses.replace(methane, source=source), FDM)
    assert loads(dumps(model)) == model
