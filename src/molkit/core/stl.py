"""Triangles -> binary STL bytes. STL has no units; slicers assume mm, so pass mm."""

from __future__ import annotations

import struct
from collections.abc import Sequence

from molkit.core.vec import Vec3

Triangle = tuple[Vec3, Vec3, Vec3]

_HEADER = b"molkit".ljust(80, b" ")
_RECORD = struct.Struct("<12fH")  # normal, three vertices, attribute byte count


def binary_stl(triangles: Sequence[Triangle]) -> bytes:
    """Binary STL with right-hand-rule normals (slicers recompute them, but some viewers don't)."""
    records = (_RECORD.pack(*_normal(t), *_coords(t), 0) for t in triangles)
    return _HEADER + struct.pack("<I", len(triangles)) + b"".join(records)


def _normal(triangle: Triangle) -> tuple[float, float, float]:
    a, b, c = triangle
    n = (b - a).cross(c - a)
    length = n.norm()
    return (n.x / length, n.y / length, n.z / length) if length > 0 else (0.0, 0.0, 0.0)


def _coords(triangle: Triangle) -> tuple[float, ...]:
    return tuple(c for v in triangle for c in (v.x, v.y, v.z))
