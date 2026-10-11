from __future__ import annotations

import struct

import pytest

from molkit.core.stl import binary_stl
from molkit.core.vec import Vec3

ORIGIN, X, Y = Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0), Vec3(0.0, 1.0, 0.0)


def test_empty_mesh_is_header_and_zero_count() -> None:
    data = binary_stl([])
    assert len(data) == 84
    assert struct.unpack_from("<I", data, 80) == (0,)


def test_layout_is_80_byte_header_count_and_50_bytes_per_triangle() -> None:
    data = binary_stl([(ORIGIN, X, Y), (ORIGIN, Y, X)])
    assert len(data) == 84 + 2 * 50
    assert struct.unpack_from("<I", data, 80) == (2,)
    assert data[:6] == b"molkit"


def test_triangle_record_holds_normal_vertices_and_zero_attribute() -> None:
    record = struct.unpack_from("<12fH", binary_stl([(ORIGIN, X, Y)]), 84)
    assert record[:3] == (0.0, 0.0, 1.0)  # right-hand rule: counter-clockwise seen from +z
    assert record[3:12] == (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    assert record[12] == 0


def test_degenerate_triangle_gets_zero_normal() -> None:
    record = struct.unpack_from("<3f", binary_stl([(ORIGIN, X, X * 2.0)]), 84)
    assert record == pytest.approx((0.0, 0.0, 0.0))
