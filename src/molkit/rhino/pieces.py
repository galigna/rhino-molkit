"""PieceSpec -> one closed Brep per atom: ball + stubs + pegs, minus holes."""

from __future__ import annotations

from Rhino.Geometry import (
    Brep,
    BrepSolidOrientation,
    Circle,
    Cylinder,
    LoftType,
    Plane,
    Point3d,
    PolylineCurve,
    Sphere,
    Vector3d,
)

from molkit.core.puzzle import Gender, Joint, PegProfile, PieceSpec, outline
from molkit.core.vec import Vec3

# Rhino booleans fail on coincident faces, so pegs start this far inside the stub and holes
# overshoot the stub's end face by the same amount.
_OVERLAP_MM = 0.5
# Geometry tolerance, independent of the document: a metre template's tolerance (~1 mm) is
# coarser than the 2 mm pegs, and capping and booleans then fail. Far below printer resolution.
_TOLERANCE_MM = 0.01


def piece_brep(piece: PieceSpec, mm: float) -> Brep | None:
    """The printable solid for one piece, or None if Rhino can't build it."""
    tolerance = _TOLERANCE_MM * mm
    pegs = [_joint_solid(piece, j, mm, tolerance) for j in piece.joints if j.gender is Gender.PEG]
    holes = [_joint_solid(piece, j, mm, tolerance) for j in piece.joints if j.gender is Gender.HOLE]
    if None in pegs or None in holes:
        return None
    solids = [Sphere(point(piece.center, mm), piece.ball_radius * mm).ToBrep()]
    solids += [_stub(piece, j, mm) for j in piece.joints] + pegs
    body = _single(Brep.CreateBooleanUnion(solids, tolerance)) if len(solids) > 1 else solids[0]
    if body is None or not holes:
        return body
    return _single(Brep.CreateBooleanDifference([body], holes, tolerance))


def _single(breps: list[Brep] | None) -> Brep | None:
    return breps[0] if breps is not None and len(breps) == 1 else None


def _stub(piece: PieceSpec, joint: Joint, mm: float) -> Brep:
    plane = Plane(point(piece.center, mm), _vector(joint.direction))
    return Cylinder(Circle(plane, piece.stick_radius * mm), joint.length * mm).ToBrep(True, True)


def _joint_solid(piece: PieceSpec, joint: Joint, mm: float, tolerance: float) -> Brep | None:
    (shaft, _), *rest = joint.sections
    start = -_OVERLAP_MM if joint.gender is Gender.PEG else _OVERLAP_MM
    return _loft(piece, joint, [(shaft, start), *rest], mm, tolerance)


def _loft(
    piece: PieceSpec,
    joint: Joint,
    sections: list[tuple[PegProfile, float]],
    mm: float,
    tolerance: float,
) -> Brep | None:
    """Closed straight loft through cross-sections at distances z (mm) past the joint midpoint,
    or None if Rhino can't loft or cap it."""
    curves = [_section(piece, joint, profile, z, mm) for profile, z in sections]
    loft = Brep.CreateFromLoft(curves, Point3d.Unset, Point3d.Unset, LoftType.Straight, False)
    solid = loft[0].CapPlanarHoles(tolerance) if loft else None
    if solid is not None and solid.SolidOrientation == BrepSolidOrientation.Inward:
        solid.Flip()  # booleans need outward normals
    return solid


def _section(
    piece: PieceSpec, joint: Joint, profile: PegProfile, z: float, mm: float
) -> PolylineCurve:
    # Plane x-axis = key_ref, so outline()'s flats face the pi direction; normal = direction.
    origin = piece.center + joint.direction * (joint.length + z)
    y_axis = joint.direction.cross(joint.key_ref)
    plane = Plane(point(origin, mm), _vector(joint.key_ref), _vector(y_axis))
    points = [plane.PointAt(x * mm, y * mm) for x, y in outline(profile)]
    return PolylineCurve(points + points[:1])


def point(v: Vec3, mm: float) -> Point3d:
    """A core Vec3 in mm as a Rhino point in document units (`mm` = doc units per mm)."""
    return Point3d(v.x * mm, v.y * mm, v.z * mm)


def _vector(v: Vec3) -> Vector3d:
    return Vector3d(v.x, v.y, v.z)
