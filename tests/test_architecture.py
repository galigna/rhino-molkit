from __future__ import annotations

import ast
from pathlib import Path

import pytest

CORE = Path(__file__).parents[1] / "src" / "molkit" / "core"
FORBIDDEN = {"Rhino", "rhinoscriptsyntax", "scriptcontext", "System", "clr", "Grasshopper"}


def forbidden_imports(source: str) -> list[str]:
    """Top-level package names in `source` that core must never import."""
    names = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return [n for n in names if n.split(".")[0] in FORBIDDEN]


@pytest.mark.parametrize("path", sorted(CORE.rglob("*.py")), ids=lambda p: p.name)
def test_core_never_imports_rhino(path: Path) -> None:
    assert forbidden_imports(path.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    "planted",
    [
        "import Rhino.Geometry",
        "from scriptcontext import doc",
        "def f():\n    import rhinoscriptsyntax as rs",
        "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import System",
    ],
)
def test_checker_catches_planted_import(planted: str) -> None:
    assert forbidden_imports(planted) != []


def test_checker_allows_rdkit_and_relative_imports() -> None:
    assert forbidden_imports("from rdkit import Chem\nfrom . import vec\nimport math") == []
