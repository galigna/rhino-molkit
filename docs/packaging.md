# Building and releasing the plugin

molkit ships as a Rhino 8 **Script Editor project**: `rhino/molkit.rhproj` bundles the command
scripts and the `molkit` package into a `.rhp` plugin and a `.yak` package. The project file is
created and built in Rhino's Script Editor; the menu names below are from Rhino 8.35 and may
differ slightly in other versions.

## 1. Create the project (once)

1. Rhino 8 → `ScriptEditor` → **File → New Project…** → save it as `<repo>\rhino\molkit.rhproj`.
2. **Project settings:**
   - Name `molkit`, version `0.1.0` (keep it equal to `version` in `pyproject.toml`)
   - Author, copyright, description: "Turns molecules into 3D-printable puzzles"
   - URL `https://github.com/galigna/rhino-molkit`, license MIT
3. **Commands:** add each existing file in `<repo>\rhino\commands\` (`MolkitFetch.py` …
   `MolkitSettings.py`). The file name becomes the command name. Their `# r:` lines make Rhino
   install RDKit and gemmi on first use.
4. **Libraries:** add the folder `<repo>\src\molkit` as a Python 3 library, so `import molkit`
   resolves to the bundled copy.
5. Save, then commit `rhino/molkit.rhproj`.

## 2. Build

In the Script Editor: **Publish → Build Project** (target Rhino 8), output folder `<repo>\build`.
That gives a `.rhp` and a `.yak` file. `build/` is git-ignored; release files go on GitHub, not
in the repo.

## 3. Test the built plugin, not the checkout

1. Disable the development setup: rename
   `%USERPROFILE%\.rhinocode\py39-rh8\lib\site-packages\molkit-dev.pth` to `molkit-dev.pth.off`.
   Otherwise Rhino still imports molkit from the repo and the test proves nothing.
2. Install the package:
   ```
   "C:\Program Files\Rhino 8\System\Yak.exe" install <repo>\build\<the .yak file>
   ```
   (or drag the `.rhp` onto a Rhino window).
3. Restart Rhino. The commands are now typed directly (`MolkitFetch`, …), no `_-RunPythonScript`.
4. Run the whole [smoke test](smoke-test.md).
5. To go back to development, uninstall (`Yak.exe uninstall molkit`) and rename the `.pth` back.

## 4. Release

1. Merge the release PR, then tag `main`: `git tag v0.1.0 && git push origin v0.1.0`.
2. Create a GitHub release for the tag and attach the `.yak` file.
3. Optional: publish to the public Yak server with `Yak.exe login` and `Yak.exe push <file>.yak`.
   This is public and can't be fully undone, so do it only when the print sizes are confirmed.

For the next version, bump `version` in both `pyproject.toml` and the project settings.
