from __future__ import annotations

import re
import runpy
import zipfile
from pathlib import Path

# tools/ is not a package; load the script's functions directly.
_tool = runpy.run_path(str(Path(__file__).parents[1] / "tools" / "fix_toolbar.py"))
fix, patch_yak = _tool["fix"], _tool["patch_yak"]

FLOATING = '<dock_bar_info visible="True" floating="True" />'
COMMANDS = ["ExportStl", "Fetch", "ImportCif", "Info", "Puzzle", "Regenerate", "Settings"]


def _item(name: str) -> str:
    return (
        f'<tool_bar_item guid="g-{name}" button_style="normal">'
        f"<text><locale_1033>Molkit{name}</locale_1033></text></tool_bar_item>"
    )


def _rui(names: list[str]) -> str:
    items = "".join(_item(n) for n in names)
    return (
        '<tool_bar_group><dock_bar_info visible="True"  floating="True" /></tool_bar_group>'
        f'<tool_bars><tool_bar guid="t"><text>molkit</text>{items}</tool_bar></tool_bars>'
    )


def _layout(rui: str) -> list[str]:
    """Toolbar items in order: command names, '|' for separators."""
    tokens = re.findall(r'Molkit(\w+)</locale_1033>|button_style="spacer"', rui)
    return [t or "|" for t in tokens]


def test_toolbar_stays_visible_and_floating_for_first_use() -> None:
    assert fix(_rui(COMMANDS)).count(FLOATING) == 1


def test_packages_patched_by_older_versions_are_reset() -> None:
    hidden = _rui(COMMANDS).replace('visible="True"', 'visible="False"')
    docked = _rui(COMMANDS).replace(
        'floating="True"', 'floating="False" docking="True" dock_location="top"'
    )
    assert FLOATING in fix(hidden)
    assert FLOATING in fix(docked)


def test_buttons_are_grouped_by_task() -> None:
    assert _layout(fix(_rui(COMMANDS))) == [
        "Fetch", "ImportCif", "|", "Info", "Regenerate", "Settings", "|", "Puzzle", "ExportStl"
    ]  # fmt: skip


def test_fixing_twice_changes_nothing() -> None:
    once = fix(_rui(COMMANDS))
    assert fix(once) == once


def test_command_missing_from_the_layout_is_kept_at_the_end() -> None:
    assert _layout(fix(_rui([*COMMANDS, "Brand"])))[-1] == "Brand"


def test_patches_the_rui_inside_the_yak_and_keeps_other_files(tmp_path: Path) -> None:
    yak = tmp_path / "molkit-0.1.1-beta-rh8-any.yak"
    with zipfile.ZipFile(yak, "w") as z:
        z.writestr("manifest.yml", "name: molkit\n")
        z.writestr("molkit.rhp", b"\x00binary")
        z.writestr("molkit.rui", _rui(COMMANDS))
    patch_yak(yak)
    with zipfile.ZipFile(yak) as z:
        assert z.read("molkit.rui").decode() == fix(_rui(COMMANDS))
        assert z.read("molkit.rhp") == b"\x00binary"
        assert z.read("manifest.yml") == b"name: molkit\n"


def test_command_in_the_layout_but_not_in_the_build_is_skipped() -> None:
    assert _layout(fix(_rui(["Fetch", "Puzzle"]))) == ["Fetch", "|", "|", "Puzzle"]
