from __future__ import annotations

import pytest

from molkit.core.errors import (
    AtomIndexError,
    MolkitError,
    UnknownElementError,
    ValidationError,
    ZeroVectorError,
)


@pytest.mark.parametrize(
    "error", [ValidationError, UnknownElementError, ZeroVectorError, AtomIndexError]
)
def test_every_error_is_a_molkit_error(error: type[Exception]) -> None:
    assert issubclass(error, MolkitError)


def test_errors_also_match_builtin_categories() -> None:
    assert issubclass(ValidationError, ValueError)
    assert issubclass(UnknownElementError, ValidationError)
    assert issubclass(ZeroVectorError, ValueError)
    assert issubclass(AtomIndexError, IndexError)
