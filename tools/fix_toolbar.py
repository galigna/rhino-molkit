"""Post-build fixes for the toolbar in the Script Editor's plugin package.

- The toolbar stays visible and floating, Script Editor's default: on first use a small molkit
  window shows beginners the buttons. Rhino then saves its state (settings/.../containers.xml),
  so once closed or docked it stays that way. Hidden, nobody finds it; a minimal "docked at the
  top" entry made Rhino 8 show nothing at all. Earlier patched packages are reset to this.
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
FLOATING = '<dock_bar_info visible="True" floating="True" />'
_SPACER = re.compile(r'\s*<tool_bar_item\b[^>]*button_style="spacer"[^>]*/>')
_ITEM = re.compile(r"<tool_bar_item\b.*?</tool_bar_item>", re.S)
_NAME = re.compile(r"<locale_1033>(\w+)</locale_1033>")


def fix(rui: str) -> str:
    """The toolbar XML visible and floating, with buttons in LAYOUT order and separators."""
    return _arrange(_DOCK_INFO.sub(FLOATING, rui))


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
    print(f"toolbar shown floating on first use and arranged in {yak.name}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
