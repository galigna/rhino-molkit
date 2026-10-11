from __future__ import annotations

import re
from pathlib import Path

import pytest
import tomli  # tomllib is 3.11+; the project runs on 3.9

ROOT = Path(__file__).parents[1]
SCRIPTS = sorted((ROOT / "rhino" / "commands").glob("*.py"))
PINS = set(tomli.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"])


def test_there_are_command_scripts() -> None:
    assert SCRIPTS


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.stem)
def test_script_runs_in_cpython_not_ironpython(script: Path) -> None:
    assert script.read_text(encoding="utf-8").splitlines()[0] == "#! python3"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.stem)
def test_script_requirements_match_pyproject_pins(script: Path) -> None:
    text = script.read_text(encoding="utf-8")
    requirements = {
        r.strip() for line in re.findall(r"^# r: (.+)$", text, re.M) for r in line.split(",")
    }
    assert requirements
    assert requirements <= PINS
