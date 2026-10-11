# Rhino smoke test

Manual checks for the Rhino adapter, which CI can't run. Run the whole list before merging any
change under `src/molkit/rhino/` or `rhino/`, and add a line for every new command or behaviour.

## One-time setup (until the Yak package exists, M13)

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
- [ ] `MolkitFetch methane`, then `MolkitPuzzle` → click it: prints `built 5 of 5 pieces`; layers
      `Molkit::methane::Pieces::C` and `…::H`. Turn off `…::BallStick` to see them clearly.
- [ ] The C piece has four round holes; each H piece has a round peg with a chamfered tip.
- [ ] Each piece is one closed solid: `What` says "closed solid polysurface".
- [ ] Pegs sit inside the matching holes with a visible gap (0.2 mm): use `Section` or
      `ClippingPlane` through a C–H bond.
- [ ] `ethylene`: the C=C joint is a D-shaped peg and hole whose flats line up (both face
      perpendicular to the molecule's plane).
- [ ] `benzene`: ring joints have two flats; C–H joints are round.
- [ ] `acetylene`: the C≡C peg is visibly thicker than the C–H pegs.
- [ ] `MolkitSettings` → `StickRadius=2.5` → Enter: prints a "wall … < 1.0" issue for each C
      hole and "no pieces built"; the old pieces are removed.
- [ ] `MolkitSettings` back to `StickRadius=3.5`: the pieces are rebuilt automatically.
- [ ] `IncludeHydrogens=No` with pieces present: methane becomes a single plain C ball piece.
