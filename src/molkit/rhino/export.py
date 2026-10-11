"""Piece objects in the document -> one STL file each, plus the assembly manifest."""

from __future__ import annotations

import os

import Rhino
from Rhino.Geometry import Brep, Mesh, MeshingParameters, Point3f

from molkit.core.manifest import manifest_json, piece_filename, safe_name
from molkit.core.model import PuzzleModel
from molkit.core.puzzle import build_pieces
from molkit.core.stl import Triangle, binary_stl
from molkit.core.vec import Vec3
from molkit.rhino import storage

# Finer than FDM or resin printers resolve; one value avoids a per-preset parameter.
_MAX_DEVIATION_MM = 0.02


def write_stl_files(
    doc: Rhino.RhinoDoc, model: PuzzleModel, folder: str, mm: float
) -> tuple[int, list[int]]:
    """Write the model's pieces and manifest into `folder` (files are overwritten).
    Returns (files written, atoms that have no piece object)."""
    breps = storage.piece_breps(doc, model.model_id)
    if not breps:
        return 0, []
    specs = build_pieces(model.molecule, model.params)
    for spec in specs:
        if spec.atom_index in breps:
            path = os.path.join(folder, piece_filename(model.molecule.name, spec))
            _write(path, binary_stl(_triangles(breps[spec.atom_index], mm)))
    manifest = os.path.join(folder, f"{safe_name(model.molecule.name)}_manifest.json")
    _write(manifest, manifest_json(model, specs).encode("utf-8"))
    return len(breps), [s.atom_index for s in specs if s.atom_index not in breps]


def _triangles(brep: Brep, mm: float) -> list[Triangle]:
    """Mesh in document units, triangles back in mm (STL is read as mm)."""
    params = MeshingParameters()
    params.Tolerance = _MAX_DEVIATION_MM * mm
    params.JaggedSeams = False  # matching seams keep the mesh watertight
    params.SimplePlanes = False
    params.RefineGrid = True
    mesh = Mesh()
    for part in Mesh.CreateFromBrep(brep, params):
        mesh.Append(part)
    mesh.Faces.ConvertQuadsToTriangles()
    v = mesh.Vertices
    return [(_vec(v[f.A], mm), _vec(v[f.B], mm), _vec(v[f.C], mm)) for f in mesh.Faces]


def _vec(p: Point3f, mm: float) -> Vec3:
    return Vec3(p.X / mm, p.Y / mm, p.Z / mm)


def _write(path: str, data: bytes) -> None:
    with open(path, "wb") as file:
        file.write(data)
