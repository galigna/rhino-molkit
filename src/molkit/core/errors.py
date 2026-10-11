"""Exception hierarchy. Every error molkit raises subclasses MolkitError."""

from __future__ import annotations


class MolkitError(Exception):
    """Base class for all molkit errors."""


class UnknownElementError(MolkitError):
    """An element symbol is not in the element table."""
