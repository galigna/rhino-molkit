"""Bodies of the Rhino commands. The scripts in rhino/commands/ only call these."""

from __future__ import annotations

import dataclasses
import os
import uuid

import Rhino
import rhinoscriptsyntax as rs
from Rhino.Input import GetResult
from Rhino.Input.Custom import GetOption, GetString, OptionDouble, OptionToggle

from molkit.core.errors import MolkitError
from molkit.core.info import describe
from molkit.core.manifest import safe_name
from molkit.core.model import Molecule, PuzzleModel, SourceInfo
from molkit.core.params import FDM, PRESETS, Params, option_name, with_preset
from molkit.core.puzzle import build_pieces, check
from molkit.core.sources.cif import parse_cif
from molkit.core.sources.pubchem import fetch_molecule
from molkit.rhino import draw, export, storage


def fetch() -> None:
    """MolkitFetch: build a ball-and-stick model of a PubChem compound."""
    asked = _ask_compound()
    if asked is None:
        return
    name, kekulize = asked
    try:
        molecule = fetch_molecule(name, kekulize)
    except MolkitError as error:
        print(f"Molkit: {error}")
        return
    _add_model(molecule)
    if molecule.source.generated_3d:
        print("Molkit: PubChem has no 3D structure for it; RDKit generated the coordinates")


def import_cif() -> None:
    """MolkitImportCif: build a ball-and-stick model of the molecule in a crystal structure."""
    path = rs.OpenFileName("Open a CIF file", "CIF files (*.cif)|*.cif|All files (*.*)|*.*||")
    if not path:
        return
    try:
        with open(path, encoding="utf-8", errors="replace") as file:
            text = file.read()
        molecule, notes = parse_cif(text, SourceInfo("cif", os.path.basename(path)))
    except (MolkitError, OSError) as error:
        print(f"Molkit: {error}")
        return
    _add_model(molecule)
    for note in notes:
        print(f"Molkit: {note}")


def _add_model(molecule: Molecule) -> None:
    doc = Rhino.RhinoDoc.ActiveDoc
    draw.add_model(doc, PuzzleModel(str(uuid.uuid4()), molecule, FDM))
    doc.Views.Redraw()
    print(
        f"Molkit: built {molecule.name} ({len(molecule.atoms)} atoms, {len(molecule.bonds)} bonds)"
    )


def info() -> None:
    """MolkitInfo: print a summary of the model an object belongs to."""
    model = _pick_model("Select any part of a molkit model")
    if model is not None:
        print(describe(model))


def regenerate() -> None:
    """MolkitRegenerate: rebuild the ball-and-stick model from the data on its anchor. Also the
    way back from a puzzle, and a repair after parts were deleted by hand."""
    model = _pick_model("Select any part of the molkit model to regenerate")
    if model is None:
        return
    doc = Rhino.RhinoDoc.ActiveDoc
    draw.clear(doc, model)
    draw.add_ballstick(doc, model)
    doc.Views.Redraw()
    print(f"Molkit: rebuilt {model.molecule.name} as a ball-and-stick model")


def settings() -> None:
    """MolkitSettings: edit a model's parameters, save them on the anchor and regenerate."""
    model = _pick_model("Select any part of the molkit model to edit")
    if model is None:
        return
    params = _ask_params(model.params)
    if params is not None:
        _redraw(dataclasses.replace(model, params=params))


def puzzle() -> None:
    """MolkitPuzzle: split a model into printable pieces, one per atom."""
    model = _pick_model("Select any part of the molkit model to split into pieces")
    if model is not None:
        _build_pieces(model)


def export_stl() -> None:
    """MolkitExportStl: write one STL per piece and an assembly manifest into a folder."""
    model = _pick_model("Select any part of the molkit model to export")
    if model is None:
        return
    doc = Rhino.RhinoDoc.ActiveDoc
    start = os.path.dirname(doc.Path) if doc.Path else None
    folder = rs.BrowseForFolder(start, "Folder for the STL files")
    if not folder:
        return
    written, missing = export.write_stl_files(doc, model, folder, draw.mm_per_unit(doc))
    if written == 0:
        print("Molkit: this model has no pieces yet; run MolkitPuzzle first")
        return
    name = safe_name(model.molecule.name)
    print(f"Molkit: wrote {written} STL files and {name}_manifest.json to {folder}")
    if missing:
        print(f"Molkit: atoms without a piece, not exported: {missing}")


def _redraw(model: PuzzleModel) -> None:
    """Rebuild a model with new settings: a puzzle stays a puzzle. If the pieces can't be built,
    show the ball-and-stick model so the molecule doesn't vanish."""
    doc = Rhino.RhinoDoc.ActiveDoc
    was_puzzle = draw.clear(doc, model)
    if not (was_puzzle and _build_pieces(model)):
        draw.add_ballstick(doc, model)
    doc.Views.Redraw()
    print(f"Molkit: regenerated {model.molecule.name}")


def _build_pieces(model: PuzzleModel) -> bool:
    """Replace the model with its puzzle pieces; False (nothing changed) if they'd misprint."""
    specs = build_pieces(model.molecule, model.params)
    issues = check(specs, model.params)
    for issue in issues:
        print(f"Molkit: {issue.message}")
    if issues:
        print("Molkit: no pieces built; adjust the parameters with MolkitSettings")
        return False
    doc = Rhino.RhinoDoc.ActiveDoc
    failed = draw.replace_pieces(doc, model, specs)
    doc.Views.Redraw()
    print(f"Molkit: built {len(specs) - len(failed)} of {len(specs)} pieces")
    if failed:
        print(f"Molkit: Rhino's booleans failed for atoms {failed}")
    return True


def _ask_params(params: Params) -> Params | None:
    """Command-line options for every Params field, plus one per preset; Enter applies."""
    get = GetOption()
    get.SetCommandPrompt("Molkit settings (Enter to apply)")
    get.AcceptNothing(True)
    while True:
        get.ClearCommandOptions()
        presets = {get.AddOption(name): preset for name, preset in PRESETS.items()}
        options = {
            f.name: _add_option(get, f.name, getattr(params, f.name))
            for f in dataclasses.fields(Params)
        }
        result = get.Get()
        params = Params(**{name: option.CurrentValue for name, option in options.items()})
        if result == GetResult.Nothing:
            return params
        if result != GetResult.Option:
            return None
        if get.OptionIndex() in presets:
            params = with_preset(params, presets[get.OptionIndex()])


def _add_option(get: GetOption, field: str, value: float) -> OptionToggle | OptionDouble:
    name = option_name(field)
    if isinstance(value, bool):
        toggle = OptionToggle(value, "No", "Yes")
        get.AddOptionToggle(name, toggle)
        return toggle
    number = OptionDouble(value, 0.001, 1000.0)  # Rhino rejects values outside the limits
    get.AddOptionDouble(name, number)
    return number


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
