"""Exception hierarchy. Every error molkit raises subclasses MolkitError."""

from __future__ import annotations


class MolkitError(Exception):
    """Base class for all molkit errors."""


class UnknownElementError(MolkitError):
    """An element symbol is not in the element table."""


class SdfParseError(MolkitError):
    """An SDF/MOL record is unreadable or uses a bond type we cannot model."""


class No3DConformerError(MolkitError):
    """A structure has only 2D coordinates, or PubChem has no 3D record for it."""


class CompoundNotFoundError(MolkitError):
    """PubChem knows no compound by that name."""


class NetworkError(MolkitError):
    """PubChem could not be reached or answered with an unexpected error."""


class ModelDataError(MolkitError):
    """Stored model data is corrupt or from an unsupported schema version."""


class CifParseError(MolkitError):
    """A CIF file is unreadable or has no atom sites."""


class NoMoleculeFoundError(MolkitError):
    """A crystal structure contains no complete, discrete molecule (e.g. a polymer)."""
