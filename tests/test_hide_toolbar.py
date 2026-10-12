from __future__ import annotations

import runpy
import zipfile
from pathlib import Path

# tools/ is not a package; load the script's functions directly.
_tool = runpy.run_path(str(Path(__file__).parents[1] / "tools" / "hide_toolbar.py"))
hide, patch_yak = _tool["hide"], _tool["patch_yak"]

RUI = '<tool_bar_group><dock_bar_info visible="True"  floating="True" /></tool_bar_group>'


def test_toolbar_is_hidden_but_stays_floating() -> None:
    assert hide(RUI) == (
        '<tool_bar_group><dock_bar_info visible="False"  floating="True" /></tool_bar_group>'
    )


def test_already_hidden_toolbar_is_unchanged() -> None:
    hidden = hide(RUI)
    assert hide(hidden) == hidden


def test_patches_the_rui_inside_the_yak_and_keeps_other_files(tmp_path: Path) -> None:
    yak = tmp_path / "molkit-0.1.1-beta-rh8-any.yak"
    with zipfile.ZipFile(yak, "w") as z:
        z.writestr("manifest.yml", "name: molkit\n")
        z.writestr("molkit.rhp", b"\x00binary")
        z.writestr("molkit.rui", RUI)
    patch_yak(yak)
    with zipfile.ZipFile(yak) as z:
        assert z.read("molkit.rui").decode() == hide(RUI)
        assert z.read("molkit.rhp") == b"\x00binary"
        assert z.read("manifest.yml") == b"name: molkit\n"
