"""Post-build fix for the Script Editor's plugin package.

Script Editor writes the toolbar as `<dock_bar_info visible="True" floating="True" />`, and Rhino
reads plugin toolbars fresh on every start, so the molkit toolbar pops up as a floating window
each time. This hides it (users open it from the toolbar list or dock it themselves) in the
built .yak and the loose .rui next to it.

    uv run python tools/hide_toolbar.py rhino/build/rh8/molkit-<version>-rh8-any.yak
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

_VISIBLE = re.compile(r'(<dock_bar_info\s+visible=")True(")')


def hide(rui: str) -> str:
    """The toolbar XML with the plugin's toolbar group hidden by default."""
    return _VISIBLE.sub(r"\1False\2", rui)


def patch_yak(yak: Path) -> None:
    """Rewrite every .rui inside the .yak archive with the toolbar hidden."""
    with zipfile.ZipFile(yak) as source:
        entries = [(info, source.read(info)) for info in source.infolist()]
    with zipfile.ZipFile(yak, "w", zipfile.ZIP_DEFLATED) as target:
        for info, data in entries:
            if info.filename.endswith(".rui"):
                data = hide(data.decode("utf-8-sig")).encode("utf-8")
            target.writestr(info, data)


def main(yak: Path) -> None:
    patch_yak(yak)
    for rui in yak.parent.glob("*.rui"):
        rui.write_text(hide(rui.read_text(encoding="utf-8-sig")), encoding="utf-8")
    print(f"toolbar hidden by default in {yak.name}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
