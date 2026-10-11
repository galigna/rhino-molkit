"""User-text tags on molkit objects, and the anchor object that stores a model's JSON."""

from __future__ import annotations

from collections.abc import Iterable

import Rhino
from Rhino.DocObjects import ObjectAttributes, ObjectEnumeratorSettings

from molkit.core.errors import ModelDataError
from molkit.core.model import PuzzleModel
from molkit.core.serialize import dumps, loads

MODEL_ID = "molkit.model_id"
ROLE = "molkit.role"  # anchor | ball | stick
ATOM_INDEX = "molkit.atom_index"
MODEL_JSON = "molkit.model"


def tagged(
    layer_index: int, model_id: str, role: str, atom_index: int | None = None
) -> ObjectAttributes:
    """Attributes for a new molkit object on `layer_index`."""
    attrs = ObjectAttributes()
    attrs.LayerIndex = layer_index
    attrs.SetUserString(MODEL_ID, model_id)
    attrs.SetUserString(ROLE, role)
    if atom_index is not None:
        attrs.SetUserString(ATOM_INDEX, str(atom_index))
    return attrs


def add_anchor(doc: Rhino.RhinoDoc, model: PuzzleModel, layer_index: int) -> None:
    """Add the point that carries the model's JSON; everything else is regenerated from it."""
    attrs = tagged(layer_index, model.model_id, "anchor")
    attrs.SetUserString(MODEL_JSON, dumps(model))
    doc.Objects.AddPoint(Rhino.Geometry.Point3d.Origin, attrs)


def model_of(doc: Rhino.RhinoDoc, obj: Rhino.DocObjects.RhinoObject) -> PuzzleModel | None:
    """The model `obj` belongs to, or None if it is not molkit geometry."""
    model_id = obj.Attributes.GetUserString(MODEL_ID)
    if not model_id:
        return None
    for candidate in _all_objects(doc):
        attrs = candidate.Attributes
        if attrs.GetUserString(MODEL_ID) == model_id and attrs.GetUserString(ROLE) == "anchor":
            return loads(attrs.GetUserString(MODEL_JSON))
    raise ModelDataError(f"the anchor of model {model_id} is missing, so it can't be read")


def _all_objects(doc: Rhino.RhinoDoc) -> Iterable[Rhino.DocObjects.RhinoObject]:
    # The anchor sits on a locked layer, which the default enumerator skips.
    settings = ObjectEnumeratorSettings()
    settings.LockedObjects = True
    settings.HiddenObjects = True
    return doc.Objects.GetObjectList(settings)
