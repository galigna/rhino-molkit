"""Bodies of the Rhino commands. The scripts in rhino/commands/ only call these."""

from __future__ import annotations

import uuid

import Rhino
from Rhino.Input import GetResult
from Rhino.Input.Custom import GetString, OptionToggle

from molkit.core.errors import MolkitError
from molkit.core.info import describe
from molkit.core.model import PuzzleModel, SourceInfo
from molkit.core.params import FDM
from molkit.core.sources.pubchem import fetch_sdf
from molkit.core.sources.sdf import parse_sdf
from molkit.rhino import draw, storage


def fetch() -> None:
    """MolkitFetch: build a ball-and-stick model of a PubChem compound."""
    asked = _ask_compound()
    if asked is None:
        return
    name, kekulize = asked
    try:
        molecule = parse_sdf(fetch_sdf(name), SourceInfo("pubchem", name), kekulize)
    except MolkitError as error:
        print(f"Molkit: {error}")
        return
    doc = Rhino.RhinoDoc.ActiveDoc
    draw.add_ballstick(doc, PuzzleModel(str(uuid.uuid4()), molecule, FDM))
    doc.Views.Redraw()
    print(f"Molkit: built {name} ({len(molecule.atoms)} atoms, {len(molecule.bonds)} bonds)")


def info() -> None:
    """MolkitInfo: print a summary of the model an object belongs to."""
    model = _pick_model("Select any part of a molkit model")
    if model is not None:
        print(describe(model))


def _ask_compound() -> tuple[str, bool] | None:
    get = GetString()
    get.SetCommandPrompt("PubChem compound name")
    kekulize = OptionToggle(False, "No", "Yes")
    get.AddOptionToggle("Kekulize", kekulize)
    while True:
        result = get.GetLiteralString()  # literal: names may contain spaces
        if result == GetResult.Option:
            continue
        name = get.StringResult().strip() if result == GetResult.String else ""
        return (name, kekulize.CurrentValue) if name else None


def _pick_model(prompt: str) -> PuzzleModel | None:
    result, ref = Rhino.Input.RhinoGet.GetOneObject(
        prompt, False, Rhino.DocObjects.ObjectType.AnyObject
    )
    if result != Rhino.Commands.Result.Success:
        return None
    try:
        model = storage.model_of(Rhino.RhinoDoc.ActiveDoc, ref.Object())
    except MolkitError as error:
        print(f"Molkit: {error}")
        return None
    if model is None:
        print("Molkit: that object is not part of a molkit model")
    return model
