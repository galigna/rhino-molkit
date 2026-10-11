"""Exception hierarchy. Every error molkit raises subclasses MolkitError."""

from __future__ import annotations


class MolkitError(Exception):
    """Base class for all molkit errors."""


class ValidationError(MolkitError, ValueError):
    """A core data object was constructed with invalid values."""


class UnknownElementError(ValidationError):
    """An element symbol is not in the element table."""


class ZeroVectorError(MolkitError, ValueError):
    """An operation needs a non-zero vector."""


class AtomIndexError(MolkitError, IndexError):
    """An atom index is out of range or not part of the given bond."""
