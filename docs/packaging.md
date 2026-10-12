# Building and releasing the plugin

molkit ships as a Rhino 8 **Script Editor project**: `rhino/molkit.rhproj` bundles the command
scripts and the `molkit` package into a `.rhp` plugin and a `.yak` package. The project file is
created and built in Rhino's Script Editor; the menu names below are from Rhino 8.35 and may
differ slightly in other versions.

## 1. Create the project (once)

1. Rhino 8 → `ScriptEditor` → **File → New Project…** → save it as `<repo>\rhino\molkit.rhproj`.
2. **Project settings:**
   - Name `molkit`, version `0.1.1-beta` (keep it equal to `version` in `pyproject.toml`).
     Script Editor rejected `0.1.0`; it accepts `major.minor.patch-suffix` and appends a
     `+build` number to the package version.
   - Author, copyright, description: "Turns molecules into 3D-printable puzzles"
   - URL `https://github.com/galigna/rhino-molkit`, license MIT
3. **Commands:** add each existing file in `<repo>\rhino\commands\` (`MolkitFetch.py` …
   `MolkitSettings.py`). The file name becomes the command name. Their `# r:` lines make Rhino
   install RDKit and gemmi on first use.
4. **Libraries:** add the folder `<repo>\src\molkit` as a Python 3 library, so `import molkit`
   resolves to the bundled copy. The committed project uses the relative path
   `"base": "../src/molkit/"`, which Script Editor resolves against the project file, so it
   builds from any clone. But Script Editor **saves it back as an absolute** `file:///` path
   into your own folder. Before committing `molkit.rhproj`, set that line back to
   `"../src/molkit/"`; `tests/test_rhino_scripts.py` fails until you do. The path never ends up
   in the built package either way.
5. **Icons:** give each command its `rhino\icons\<Command>.svg` in **both** the Light and the
   Dark slot; an empty slot leaves a blank button in that theme. The project embeds the icons,
   so the SVGs in `rhino/icons/` are the editable sources.
6. Save, then commit `rhino/molkit.rhproj`.

## 2. Build

In the Script Editor: **Publish → Build Project** (target Rhino 8). The output lands in
`<repo>\rhino\build\rh8\`: a `.rhp`, a `.yak` and the package's `manifest.yml`. `build/` is
git-ignored; release files go on GitHub, not in the repo.

**Then, after every build**, fix the toolbar:

```bash
uv run python tools/fix_toolbar.py rhino/build/rh8/<the .yak file>
```

- It **docks the toolbar at the top.** Script Editor marks it floating, and Rhino reads plugin
  toolbars fresh on each start, so otherwise it pops up over the template window every time
  Rhino opens. Hiding it instead would leave beginners without buttons.
- It **orders the buttons and adds separators** (Script Editor can't): get a molecule
  (Fetch, ImportCif) | look and change (Info, Regenerate, Settings) | puzzle (Puzzle,
  ExportStl). The order is `LAYOUT` at the top of the script; a new command not listed there
  goes at the end.

## 3. Test the built plugin, not the checkout

1. Disable the development setup: rename
   `%USERPROFILE%\.rhinocode\py39-rh8\lib\site-packages\molkit-dev.pth` to `molkit-dev.pth.off`.
   Otherwise Rhino still imports molkit from the repo and the test proves nothing.
2. Install the package (PowerShell; `&` runs a quoted program path):
   ```powershell
   & "C:\Program Files\Rhino 8\System\Yak.exe" install "<repo>\rhino\build\rh8\<the .yak file>"
   ```
   (or drag the `.rhp` onto a Rhino window).
3. Restart Rhino. The commands are now typed directly (`MolkitFetch`, …), no `_-RunPythonScript`.
4. Run the whole [smoke test](smoke-test.md).
5. To go back to development, uninstall (`Yak.exe uninstall molkit`) and rename the `.pth` back.

## 4. Release

1. Merge the release PR, then tag `main`: `git tag v0.1.1-beta && git push origin v0.1.1-beta`.
2. Create a GitHub release for the tag and attach the `.yak` file.
3. Optional: publish to the public Yak server with `Yak.exe login` and `Yak.exe push <file>.yak`.
   This is public and can't be fully undone, so do it only when the print sizes are confirmed.

For the next version, bump `version` in both `pyproject.toml` and the project settings.
