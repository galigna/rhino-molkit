"""Exception hierarchy. Every error molkit raises subclasses MolkitError."""

from __future__ import annotations


class MolkitError(Exception):
    """Base class for all molkit errors."""


class UnknownElementError(MolkitError):
    """An element symbol is not in the element table."""


class SdfParseError(MolkitError):
    """An SDF/MOL record is unreadable or uses a bond type we cannot model."""


class No3DConformerError(MolkitError):
    """A structure has only 2D coordinates."""
