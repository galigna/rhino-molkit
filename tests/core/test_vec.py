from __future__ import annotations

import pytest

from molkit.core.vec import Vec3

A = Vec3(1.0, 2.0, 3.0)
B = Vec3(-4.0, 5.0, 0.5)
X = Vec3(1.0, 0.0, 0.0)
Y = Vec3(0.0, 1.0, 0.0)


def test_add_and_sub() -> None:
    assert A + B == Vec3(-3.0, 7.0, 3.5)
    assert A - B == Vec3(5.0, -3.0, 2.5)


def test_scalar_mul() -> None:
    assert A * 2 == Vec3(2.0, 4.0, 6.0)


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
