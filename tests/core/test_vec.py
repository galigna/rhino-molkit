from __future__ import annotations

import dataclasses
import math

import pytest

from molkit.core.errors import ZeroVectorError
from molkit.core.vec import Vec3

A = Vec3(1.0, 2.0, 3.0)
B = Vec3(-4.0, 5.0, 0.5)
X = Vec3(1.0, 0.0, 0.0)
Y = Vec3(0.0, 1.0, 0.0)
ZERO = Vec3(0.0, 0.0, 0.0)


def test_add_and_sub() -> None:
    assert A + B == Vec3(-3.0, 7.0, 3.5)
    assert A - B == Vec3(5.0, -3.0, 2.5)


def test_neg() -> None:
    assert -A == Vec3(-1.0, -2.0, -3.0)


def test_scalar_mul_works_on_both_sides() -> None:
    assert A * 2 == Vec3(2.0, 4.0, 6.0)
    assert 2 * A == A * 2


def test_dot() -> None:
    assert A.dot(B) == pytest.approx(-4.0 + 10.0 + 1.5)
    assert X.dot(Y) == 0.0


def test_cross_follows_right_hand_rule() -> None:
    assert X.cross(Y) == Vec3(0.0, 0.0, 1.0)
    assert Y.cross(X) == Vec3(0.0, 0.0, -1.0)


def test_norm() -> None:
    assert Vec3(3.0, 4.0, 0.0).norm() == pytest.approx(5.0)


def test_unit_has_length_one_and_same_direction() -> None:
    u = A.unit()
    assert u.norm() == pytest.approx(1.0)
    assert u.dot(A) == pytest.approx(A.norm())


def test_unit_of_zero_vector_raises() -> None:
    with pytest.raises(ZeroVectorError):
        ZERO.unit()


def test_distance_to() -> None:
    assert A.distance_to(B) == pytest.approx((A - B).norm())
    assert A.distance_to(A) == 0.0


@pytest.mark.parametrize(
    ("other", "expected_deg"),
    [(Y, 90.0), (X * 3, 0.0), (-X, 180.0), (Vec3(1.0, 1.0, 0.0), 45.0)],
)
def test_angle_to(other: Vec3, expected_deg: float) -> None:
    assert math.degrees(X.angle_to(other)) == pytest.approx(expected_deg, abs=1e-9)


def test_angle_to_parallel_vectors_survives_rounding() -> None:
    v = Vec3(0.1, 0.2, 0.3)
    assert v.angle_to(v * 3.0) == pytest.approx(0.0, abs=1e-6)


def test_angle_to_zero_vector_raises() -> None:
    with pytest.raises(ZeroVectorError):
        X.angle_to(ZERO)


def test_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        A.x = 9.0  # type: ignore[misc]
