"""Draw core specs into a Rhino document: per-element layers, one block per ball size, sticks."""

from __future__ import annotations

import Rhino
import System
from Rhino.DocObjects import Layer, ObjectAttributes, ObjectColorSource
from Rhino.Geometry import Brep, Circle, Cylinder, Plane, Point3d, Sphere, Transform, Vector3d
from System.Drawing import Color

from molkit.core.ballstick import BallSpec, StickSpec, build
from molkit.core.model import PuzzleModel
from molkit.core.vec import Vec3
from molkit.rhino import storage

_DATA_LAYER_COLOR = (128, 128, 128)


def add_model(doc: Rhino.RhinoDoc, model: PuzzleModel) -> None:
    """Draw a new model and add the anchor that stores it."""
    _add_ballstick(doc, model)
    data_layer = _layer(doc, f"{_root(model)}::_data", _DATA_LAYER_COLOR, locked=True)
    storage.add_anchor(doc, model, data_layer)


def redraw(doc: Rhino.RhinoDoc, model: PuzzleModel) -> None:
    """Replace an existing model's geometry and save `model` (e.g. new params) on its anchor."""
    storage.delete_generated(doc, model.model_id)
    _add_ballstick(doc, model)
    storage.update_anchor(doc, model)


def _add_ballstick(doc: Rhino.RhinoDoc, model: PuzzleModel) -> None:
    mm = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Millimeters, doc.ModelUnitSystem)
    parent = f"{_root(model)}::BallStick"
    spec = build(model.molecule, model.params)
    for ball in spec.balls:
        _add_ball(doc, model.model_id, parent, ball, mm)
    for stick in spec.sticks:
        _add_stick(doc, model.model_id, parent, stick, mm)


def _root(model: PuzzleModel) -> str:
    return f"Molkit::{model.molecule.name}"


def _add_ball(doc: Rhino.RhinoDoc, model_id: str, parent: str, ball: BallSpec, mm: float) -> None:
    layer = _layer(doc, f"{parent}::{ball.element}", ball.color_rgb)
    attrs = storage.tagged(layer, model_id, "ball", ball.atom_index)
    block = _ball_block(doc, ball.element, ball.radius * mm)
    move = Transform.Translation(Vector3d(_point(ball.center, mm)))
    doc.Objects.AddInstanceObject(block, move, attrs)


def _add_stick(
    doc: Rhino.RhinoDoc, model_id: str, parent: str, stick: StickSpec, mm: float
) -> None:
    layer = _layer(doc, f"{parent}::{stick.element}", stick.color_rgb)
    attrs = storage.tagged(layer, model_id, "stick", stick.atom_index)
    doc.Objects.AddBrep(_cylinder(stick, mm), attrs)


def _ball_block(doc: Rhino.RhinoDoc, element: str, radius: float) -> int:
    # One definition per element and size, shared by every model that uses it.
    name = f"Molkit ball {element} {radius:.3f}"
    existing = doc.InstanceDefinitions.Find(name)
    if existing is not None:
        return int(existing.Index)
    attrs = ObjectAttributes()
    attrs.ColorSource = ObjectColorSource.ColorFromParent  # instance takes its layer's colour
    sphere = Sphere(Point3d.Origin, radius).ToBrep()
    return int(doc.InstanceDefinitions.Add(name, "molkit", Point3d.Origin, [sphere], [attrs]))


def _cylinder(stick: StickSpec, mm: float) -> Brep:
    start, end = _point(stick.start, mm), _point(stick.end, mm)
    axis = end - start
    return Cylinder(Circle(Plane(start, axis), stick.radius * mm), axis.Length).ToBrep(True, True)


def _layer(
    doc: Rhino.RhinoDoc, path: str, color_rgb: tuple[int, int, int], locked: bool = False
) -> int:
    """Index of the layer at `path` ("A::B::C"), creating missing levels. Only a newly created
    leaf gets the colour and lock, so user changes to existing layers survive."""
    names = path.split("::")
    parent_id = System.Guid.Empty
    index = -1
    for depth in range(1, len(names) + 1):
        index = doc.Layers.FindByFullPath("::".join(names[:depth]), -1)
        if index < 0:
            layer = Layer()
            layer.Name = names[depth - 1]
            layer.ParentLayerId = parent_id
            if depth == len(names):
                layer.Color = Color.FromArgb(*color_rgb)
                layer.IsLocked = locked
            index = doc.Layers.Add(layer)
        parent_id = doc.Layers[index].Id
    return index


def _point(v: Vec3, mm: float) -> Point3d:
    return Point3d(v.x * mm, v.y * mm, v.z * mm)
