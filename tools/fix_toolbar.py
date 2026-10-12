"""Post-build fixes for the toolbar in the Script Editor's plugin package.

- Script Editor writes the toolbar as `<dock_bar_info visible="True" floating="True" />`, and
  Rhino reads plugin toolbars fresh on every start, so it pops up as a floating window over the
  template dialog each time; hidden instead, beginners would never find it. So it is docked at
  the top, visible, with the attributes of Rhino's own default top toolbar (from Rhino.UI.dll).
- Script Editor orders the buttons like the project's command list and has no separators.
  This applies LAYOUT, using Rhino's own separator: `<tool_bar_item ... button_style="spacer" />`.

    uv run python tools/fix_toolbar.py rhino/build/rh8/molkit-<version>-rh8-any.yak
"""

from __future__ import annotations

import re
import sys
import uuid
import zipfile
from pathlib import Path

SEPARATOR = "|"
# Get a molecule | look at and change it | make the puzzle.
LAYOUT = [
    "MolkitFetch",
    "MolkitImportCif",
    SEPARATOR,
    "MolkitInfo",
    "MolkitRegenerate",
    "MolkitSettings",
    SEPARATOR,
    "MolkitPuzzle",
    "MolkitExportStl",
]

_DOCK_INFO = re.compile(r"<dock_bar_info\b[^>]*/>")
# 59419 is the id Rhino's own default toolbar file uses for its top dock bar.
DOCKED = (
    '<dock_bar_info visible="True" floating="False" docking="True" '
    'dock_location_u="59419" dock_location="top" />'
)
_SPACER = re.compile(r'\s*<tool_bar_item\b[^>]*button_style="spacer"[^>]*/>')
_ITEM = re.compile(r"<tool_bar_item\b.*?</tool_bar_item>", re.S)
_NAME = re.compile(r"<locale_1033>(\w+)</locale_1033>")


def fix(rui: str) -> str:
    """The toolbar XML docked at the top, with buttons in LAYOUT order and separators."""
    return _arrange(_DOCK_INFO.sub(DOCKED, rui))


def _arrange(rui: str) -> str:
    rui = _SPACER.sub("", rui)
    items = _ITEM.findall(rui)
    if not items:
        return rui
    start, end = rui.index(items[0]), rui.rindex(items[-1]) + len(items[-1])
    by_name = {_NAME.search(item).group(1): item for item in items}
    ordered = [
        _spacer(i) if name == SEPARATOR else by_name.pop(name)
        for i, name in enumerate(LAYOUT)
        if name == SEPARATOR or name in by_name  # skip commands this build doesn't have
    ]
    return rui[:start] + "\n".join([*ordered, *by_name.values()]) + rui[end:]


def _spacer(position: int) -> str:
    # Stable ids, so every build writes the same file.
    guid = uuid.uuid5(uuid.NAMESPACE_URL, f"molkit-toolbar-separator-{position}")
    return f'<tool_bar_item guid="{guid}" button_style="spacer" />'


def patch_yak(yak: Path) -> None:
    """Rewrite every .rui inside the .yak archive."""
    with zipfile.ZipFile(yak) as source:
        entries = [(info, source.read(info)) for info in source.infolist()]
    with zipfile.ZipFile(yak, "w", zipfile.ZIP_DEFLATED) as target:
        for info, data in entries:
            if info.filename.endswith(".rui"):
                data = fix(data.decode("utf-8-sig")).encode("utf-8")
            target.writestr(info, data)


def main(yak: Path) -> None:
    patch_yak(yak)
    for rui in yak.parent.glob("*.rui"):
        rui.write_text(fix(rui.read_text(encoding="utf-8-sig")), encoding="utf-8")
    print(f"toolbar docked at the top and arranged in {yak.name}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
