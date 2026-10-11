"""Immutable 3D vector."""

from __future__ import annotations

import math
from dataclasses import dataclass

from molkit.core.errors import ZeroVectorError

_EPS = 1e-12


@dataclass(frozen=True)
class Vec3:
    """A point or direction in 3D space."""

    x: float
    y: float
    z: float

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vec3) -> Vec3:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self) -> Vec3:
        return Vec3(-self.x, -self.y, -self.z)

    def __mul__(self, k: float) -> Vec3:
        return Vec3(self.x * k, self.y * k, self.z * k)

    def __rmul__(self, k: float) -> Vec3:
        return self * k

    def dot(self, other: Vec3) -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vec3) -> Vec3:
        """Cross product (right-handed)."""
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def norm(self) -> float:
        """Euclidean length."""
        return math.sqrt(self.dot(self))

    def unit(self) -> Vec3:
        """Vector of length 1 in the same direction."""
        return self * (1.0 / self._nonzero_norm())

    def distance_to(self, other: Vec3) -> float:
        """Distance between two points."""
        return (self - other).norm()

    def angle_to(self, other: Vec3) -> float:
        """Angle between two directions, in radians."""
        cosine = self.dot(other) / (self._nonzero_norm() * other._nonzero_norm())
        return math.acos(max(-1.0, min(1.0, cosine)))

    def _nonzero_norm(self) -> float:
        n = self.norm()
        if n < _EPS:
            raise ZeroVectorError(f"zero-length vector has no direction: {self}")
        return n
