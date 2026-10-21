# Rhino smoke test

Manual checks for the Rhino adapter, which CI can't run. Run the whole list before merging any
change under `src/molkit/rhino/` or `rhino/`, and add a line for every new command or behaviour.

## One-time setup for running from a checkout

Testing an installed build instead? Follow [packaging.md](packaging.md) step 3, then skip to the
checklist and type the commands directly.


1. Make `molkit` importable in Rhino's Python: create
   `%USERPROFILE%\.rhinocode\py39-rh8\lib\site-packages\molkit-dev.pth` containing one line, the
   full path of `<repo>\src`. Rhino reads `.pth` files at startup, so this works for
   `_-RunPythonScript` too; the Script Editor's module search paths setting did not. Delete the
   file to undo.
2. Install the pinned packages once by running any command below. Rhino's pip times out after
   15 s, so if the first install fails on a slow connection, just run it again.
3. Optional: add aliases in **Rhino Options → Aliases**, for example
   `MolkitFetch` → `! _-RunPythonScript "<repo>\rhino\commands\MolkitFetch.py"`.
   Without aliases, run that macro directly.

Rhino caches imported modules: **restart Rhino after pulling new molkit code.**

## Checklist

Start each run in a new document with units set to **millimetres**.

### MolkitFetch
- [ ] `MolkitFetch` → `methane`: a grey 8.5 mm C ball, four white 6 mm H balls, half-sticks grey
      on the C side and white on the H side, radius 3.5 mm.
- [ ] Layers: `Molkit::methane::BallStick::C`, `…::H` (CPK colours) and a locked
      `Molkit::methane::_data` holding one point at the origin.
- [ ] Balls are block instances: `Molkit ball C 8.500` and `Molkit ball H 6.000`.
- [ ] Attribute User Text on any ball: `molkit.model_id`, `molkit.role = ball`,
      `molkit.atom_index`.
- [ ] `MolkitFetch` → `acetic acid` (name with a space) builds a model.
- [ ] `MolkitFetch` → `notacompound` prints "PubChem has no compound named …"; nothing is drawn.
- [ ] `MolkitFetch` → `sodium chloride` prints "PubChem has no 3D structure …"; nothing is drawn.
- [ ] Units: in a new document set to **centimetres**, `MolkitFetch methane` gives a 0.85 cm C ball.

### MolkitInfo
- [ ] `MolkitInfo` → click a methane ball: prints `methane (CH4), from PubChem 'methane'`,
      `5 atoms, 4 bonds: 4 single`, the model id and all parameters.
- [ ] `MolkitFetch` → click `Kekulize=Yes` → `benzene`; `MolkitInfo` on it shows
      `9 single, 3 double`. Without Kekulize: `6 single, 6 aromatic`.
- [ ] `MolkitInfo` → click a non-molkit object: "that object is not part of a molkit model".
- [ ] Unlock `_data`, delete the anchor point, then `MolkitInfo` on a ball: "the anchor of model
      … is missing".

### MolkitSettings
- [ ] `MolkitSettings` → click a methane ball: options `FDM`, `Resin` and one per parameter
      (`Scale`, `BallRadiusFactor`, `StickRadius`, `IncludeHydrogens`, …) show current values.
- [ ] Set `Scale=30`, press Enter: the model rebuilds 1.5× larger (C ball 12.75 mm); no old
      geometry is left behind; `MolkitInfo` shows `scale_mm_per_a = 30.0`.
- [ ] `IncludeHydrogens=No`, Enter: only the C ball remains, with no sticks.
- [ ] `IncludeHydrogens=No`, then click `Resin`: values switch to the resin preset (scale 12)
      but `IncludeHydrogens` stays `No`.
- [ ] Typing `0` for `Clearance` is rejected by Rhino (minimum 0.001).
- [ ] Esc during the prompt: nothing changes.
- [ ] Lock or hide the `BallStick::C` layer, then change a setting: the old C ball is still
      replaced (no duplicates).

### MolkitRegenerate
- [ ] Delete one H ball by hand, then `MolkitRegenerate` → click any part: all five balls are back.
- [ ] Save, close and reopen the file; `MolkitRegenerate` still works (data lives on the anchor).

### MolkitPuzzle
- [ ] `MolkitFetch methane`, then `MolkitPuzzle` → click it: prints `built 5 of 5 pieces`; the
      ball-and-stick model is replaced by pieces on `Molkit::methane::Pieces::C` and `…::H`.
- [ ] The C piece has four round holes; each H piece has a round peg with a chamfered tip.
- [ ] Each hole has three thin ribs along its length (look into it from the end, or `Section`
      across a C–H bond): they overlap the peg by 0.1 mm.
- [ ] Each piece is one closed solid: `What` says "closed solid polysurface".
- [ ] Pegs sit inside the matching holes with a visible gap (0.2 mm): use `Section` or
      `ClippingPlane` through a C–H bond.
- [ ] `ethylene`: the C=C joint is a D-shaped peg and hole whose flats line up (both face
      perpendicular to the molecule's plane).
- [ ] `benzene`: ring joints have two flats; C–H joints are round.
- [ ] `acetylene`: the C≡C peg is visibly thicker than the C–H pegs.
- [ ] In a **Meters** and a **Centimeters** document: `benzene` → `MolkitPuzzle` builds all 12
      pieces (the geometry tolerance must not come from the document).
- [ ] `MolkitSettings` → `Scale=30` on the puzzle: only pieces are rebuilt (bigger); no
      ball-and-stick model comes back.
- [ ] `MolkitSettings` → `StickRadius=2.5` → Enter: prints a "wall … < 1.0" issue for each C
      hole and "no pieces built"; the ball-and-stick model is shown instead.
- [ ] `MolkitPuzzle` on that model again: still "no pieces built", and the ball-and-stick model
      stays (nothing is deleted when the check fails).
- [ ] `MolkitSettings` back to `StickRadius=3.5`, then `MolkitPuzzle`: pieces replace the model.
- [ ] `IncludeHydrogens=No` on the puzzle: methane becomes a single plain C ball piece.
- [ ] `MolkitRegenerate` on the puzzle turns it back into the ball-and-stick model.

### MolkitExportStl
- [ ] On methane with pieces: `MolkitExportStl` → click it → pick an empty folder: prints
      `wrote 5 STL files and methane_manifest.json`.
- [ ] Folder holds `methane_000_C.stl` … `methane_004_H.stl` and `methane_manifest.json`.
- [ ] A slicer (or Rhino `Import`) opens `methane_000_C.stl` as one watertight solid with four
      round holes, 17 mm across (8.5 mm radius ball), in mm, not scaled.
- [ ] In a **centimetre** document, the exported C piece is still 17 mm across in the slicer.
- [ ] The manifest lists each file with its joints (partner atom, bond order, peg/hole, shape).
- [ ] On a model without pieces: "this model has no pieces yet; run MolkitPuzzle first", and no
      files are written.
- [ ] Cancel the folder dialog: nothing happens.

### 3D fallback (M10b)
- [ ] `MolkitFetch` → `alpha-cyclodextrin`: after a second or two it builds a ring of six glucose
      units and prints "PubChem has no 3D structure for it; RDKit generated the coordinates".
- [ ] `MolkitInfo` on it: first line ends with "3D coordinates generated by RDKit".
- [ ] `MolkitFetch methane` still uses PubChem's 3D record (no "generated" message).
- [ ] A model saved in a file from before this change still opens with `MolkitInfo`.

### MolkitImportCif
The test files are in `<repo>\tests\fixtures`.
- [ ] `MolkitImportCif` → `aspirin_cod2104857.cif`: one whole aspirin molecule (21 atoms,
      21 bonds), layers under `Molkit::aspirin_cod2104857`; no notes printed.
- [ ] `MolkitInfo` on it: `aspirin_cod2104857 (C9H8O4), from CIF 'aspirin_cod2104857.cif'`,
      `6 aromatic` and `2 double` bonds.
- [ ] `MolkitPuzzle` on it builds 21 pieces (or lists printability issues).
- [ ] `methane_split.cif`: one whole methane, not pieces scattered across the cell.
- [ ] `co2.cif`: builds, and prints "the file has no hydrogen positions, so the model has none".
- [ ] `carbon_chain.cif`: prints "… has no discrete molecule (a polymer or framework?)";
      nothing is drawn.
- [ ] Cancel the file dialog: nothing happens.

### Toolbar (installed build)
Toolbar defaults only apply where Rhino has never seen molkit's toolbar file; to test them on a
machine that has, reset its saved state as described in packaging.md.
- [ ] First start: a small floating molkit window with the buttons appears.
- [ ] Close it, restart Rhino: it stays closed. Or drag it to an edge to dock it, restart: it
      stays docked.
- [ ] Docked molkit toolbar order: Fetch, ImportCif | Info, Regenerate, Settings | Puzzle,
      ExportStl, with two separators.
