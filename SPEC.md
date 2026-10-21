# molkit — Molecular Puzzle Generator for Rhino 8

## 1. Goal

A Rhino 8 plugin (CPython 3) that turns a molecule into a **3D-printable puzzle**:

1. Load a molecule by name from **PubChem** (3D SDF) or from a **CIF** file.
2. Build an accurate **ball-and-stick** model in Rhino.
3. Split it into **one piece per atom**. Each piece is a ball with fused half-bonds. Neighbouring
   pieces join at the bond **midpoint**, peg into hole, and the peg's shape encodes the **bond order**.
4. Export each piece as an **STL**, plus a manifest describing how to assemble them.

**Reference molecule: methane (CH₄).** Each vertical slice is proven on methane first: 5 atoms,
4 single C–H bonds, tetrahedral geometry. More complex molecules come in only to exercise features
methane can't cover, such as double, triple, and aromatic bonds.

## 2. MVP scope

- PubChem lookup by compound name, using the 3D conformer record.
- CIF import of **molecular crystals**: symmetry expansion, bond perception, and extraction of one
  complete molecule.
- Ball-and-stick model: element-coloured balls (one block per element), half-bonds coloured by atom,
  and one layer per element.
- Puzzle pieces:
  - one piece per atom, with half-bonds aligned to the real bond vectors;
  - the joint sits at the bond midpoint, the heavier atom's half gets the hole, and the lighter
    atom's half gets the peg;
  - peg profiles that follow how each bond rotates (§7);
  - adjustable clearance, with **FDM** and **Resin** presets.
- Explicit hydrogens on by default, with a parameter to turn them off.
- STL export (one file per piece) and a JSON assembly manifest.
- The molecule and parameters are stored on a Rhino object, so models can be **regenerated** after a
  parameter change.
- Packaged as a Rhino 8 Script Editor project, built into a Yak package.

## 3. Non-goals (MVP)

- **Ring assembly.** Every joint is a straight push-fit along its own bond axis, so the last bond in
  a ring can only close if the plastic flexes or there is enough clearance. This is a known
  limitation and is documented in the README (see §11, post-MVP).
- Extended or covalent frameworks (MOFs, silicates, metals), unit-cell or cluster cutting, and
  dangling-bond handling.
- Engraved labels, flat print bases, and automatic support or orientation planning.
- Magnets, separate connector pieces, and other joint styles.
- Grasshopper components and a GUI panel. Interaction is through Rhino commands only.
- Hand-editing generated geometry. Edits are overwritten when the model is regenerated.
- Rhino 7 / IronPython.

## 4. Architecture

```
repo/
├─ src/molkit/
│  ├─ core/                  # pure Python: no Rhino imports, ever
│  │  ├─ vec.py              # Vec3 + vector math
│  │  ├─ elements.py         # element table (radii, colours, mass)
│  │  ├─ model.py            # Atom, Bond, BondOrder, Molecule
│  │  ├─ params.py           # Params + FDM/RESIN presets
│  │  ├─ serialize.py        # JSON round-trip with schema version
│  │  ├─ errors.py           # MolkitError hierarchy
│  │  ├─ sources/
│  │  │  ├─ sdf.py           # SDF/MOL block -> Molecule (RDKit)
│  │  │  ├─ pubchem.py       # PUG REST client (injectable HTTP)
│  │  │  └─ cif.py           # CIF -> Molecule (gemmi + RDKit)
│  │  ├─ ballstick.py        # Molecule + Params -> BallStickSpec
│  │  ├─ info.py             # formula + MolkitInfo summary
│  │  ├─ puzzle.py           # pieces: gender, key reference, profiles; printability check
│  │  ├─ manifest.py         # assembly manifest
│  │  └─ stl.py              # triangles -> binary STL bytes
│  └─ rhino/                 # thin adapter: specs -> Rhino geometry
│     ├─ draw.py             # layers, unit scaling, ball blocks, specs -> Breps
│     ├─ storage.py          # user-text tags + anchor object I/O
│     ├─ pieces.py           # PieceSpec -> closed Brep (loft sections, booleans)
│     ├─ export.py           # Mesh -> triangles -> core.stl (M10)
│     └─ commands.py         # command bodies (get input, call core, draw)
├─ rhino/
│  ├─ molkit.rhproj          # Script Editor project (build -> .rhp + .yak)
│  └─ commands/              # one-line entry scripts per Rhino command
├─ tests/
│  ├─ core/                  # pytest, mirrors src/molkit/core
│  ├─ fixtures/              # methane.sdf, benzene.sdf, ethylene.sdf, *.cif …
│  └─ test_architecture.py   # fails if core imports Rhino
├─ docs/images/
├─ pyproject.toml  README.md  SPEC.md  CLAUDE.md  LICENSE
└─ .github/workflows/ci.yml  # ruff + mypy + pytest on Python 3.9
```

**Data flow**

```
name ─► pubchem.fetch_sdf ─► sdf.parse ─┐
CIF  ─► cif.parse_cif ────────────────────┴─► Molecule ─┬─► ballstick.build ─► BallStickSpec ─► rhino.geometry
                                                      └─► puzzle.build_pieces ► PieceSpec[] ───► rhino.geometry ─► rhino.export ─► stl.write
```

**Boundary rule:** `core` returns plain frozen dataclasses that hold every number the geometry
needs: centres, radii, directions, lengths, and profile dimensions. `rhino` only turns those specs
into Rhino objects. It makes **no chemistry or puzzle decisions**, so all of the logic stays
testable without Rhino.

**Runtime:** Rhino 8 runs CPython **3.9**, so all code targets 3.9. `rdkit` and `gemmi` are **hard
dependencies**, declared as Script Editor package requirements and pinned to versions that ship
cp39 wheels for Windows and macOS: `rdkit==2025.9.2` (the last RDKit release supporting 3.9) and
`gemmi==0.7.5`.

## 5. Data model (core)

All of these are `@dataclass(frozen=True)`. Collections are `tuple`s. Coordinates are in **Å** in
the molecule and in **mm** in the specs.

```python
class BondOrder(Enum): SINGLE, DOUBLE, TRIPLE, AROMATIC

Vec3(x: float, y: float, z: float)                  # +, -, *, dot, cross, norm, unit

Element(symbol, atomic_number, mass, covalent_radius, vdw_radius, color_rgb)

Atom(element: str, position: Vec3)                  # element: canonical symbol, e.g. "Cl"
Bond(a: int, b: int, order: BondOrder)              # indices into Molecule.atoms, either order
SourceInfo(kind: Literal["pubchem", "cif"], identifier: str, generated_3d: bool = False)
Molecule(name: str, atoms: tuple[Atom, ...], bonds: tuple[Bond, ...], source: SourceInfo)
    .neighbors(i) -> tuple[int, ...]

Params(scale_mm_per_a, ball_radius_factor, stick_radius_mm, include_hydrogens, peg_radius_mm,
       triple_peg_radius_mm, flat_depth_mm, peg_length_mm, hole_extra_depth_mm, clearance_mm,
       chamfer_mm, ridge_height_mm, min_wall_mm)                     # FDM and RESIN are preset instances

BallSpec(atom_index, center: Vec3, radius, color_rgb, element)
StickSpec(atom_index, bond_index, start: Vec3, end: Vec3, radius, color_rgb)   # half-bond
BallStickSpec(balls: tuple[BallSpec, ...], sticks: tuple[StickSpec, ...])
# Hiding hydrogens skips them; atom_index/bond_index always point into the stored Molecule,
# so Rhino user strings stay valid whatever the parameters.

class Gender(Enum): PEG, HOLE
class ProfileKind(Enum): ROUND, D_FLAT, DOUBLE_FLAT
PegProfile(kind, radius, flat_depth)                # flat_depth unused for ROUND
Joint(bond_index, partner_index, direction: Vec3,   # unit vector, piece centre -> partner
      key_ref: Vec3,                                # unit, ⟂ direction; shared by both halves
      length,                                       # centre -> bond midpoint (stub end)
      gender, profile,                              # hole profiles already include clearance
      depth, chamfer,                               # peg length / hole depth; peg lead-in
      sections)                                     # ((profile, z mm past the midpoint), ...) to loft
PieceSpec(atom_index, element, center, ball_radius, stick_radius, color_rgb, joints: tuple[Joint, ...])
Issue(atom_index, message)                          # from puzzle.check(pieces, params)

PuzzleModel(model_id: str, molecule: Molecule, params: Params)   # what is persisted
```

**Persistence:** `serialize.dumps(PuzzleModel) -> str` and `serialize.loads(str) -> PuzzleModel`
write JSON that includes `schema_version`. Unknown versions and corrupt data raise `ModelDataError`.

**Storage in Rhino:** each model gets one **anchor** object, a point at the world origin on the
locked layer `Molkit::<name>::_data`. Its Attribute User Text `molkit.model` holds the serialized
`PuzzleModel`. Every molkit object, the anchor included, carries the user text `molkit.model_id`
and `molkit.role` (`anchor|ball|stick|piece`); balls, sticks and pieces also carry
`molkit.atom_index`. Copying the anchor between files copies the model. Regenerating deletes
everything with that `model_id` except the anchor, then rebuilds.

## 6. Commands

| Command | Does |
|---|---|
| `MolkitFetch` | Asks for a compound name (option: `Kekulize`), fetches the PubChem 3D SDF, and builds the ball-and-stick model plus its anchor. |
| `MolkitImportCif` | Picks a `.cif` file, extracts one molecule, and builds the ball-and-stick model plus its anchor. |
| `MolkitPuzzle` | Picks a model's anchor or any object in the model, then replaces the model's geometry with puzzle pieces on `Molkit::<name>::Pieces` (the ball-and-stick model is deleted; `MolkitRegenerate` can rebuild it from the anchor). If `puzzle.check` reports issues, they are printed and nothing is changed. `MolkitSettings` keeps a puzzle a puzzle, falling back to ball-and-stick if the new settings can't make printable pieces. |
| `MolkitSettings` | Picks a model and edits its parameters with command-line options generated from the `Params` fields (number options limited to 0.001–1000), plus `FDM`/`Resin` options that apply a preset but keep the hydrogen choice. Enter saves to the anchor and regenerates. |
| `MolkitRegenerate` | Picks a model and rebuilds it as ball-and-stick from the anchor data: the way back from a puzzle, and a repair after parts were deleted. |
| `MolkitExportStl` | Picks a model and a folder. Writes `<name>_<idx:03>_<El>.stl` for each piece and `<name>_manifest.json`. |
| `MolkitInfo` | Picks a model and prints the formula, atom and bond counts, source, and parameters. |

**Layers:** `Molkit::<name>::BallStick::<El>` and `Molkit::<name>::Pieces::<El>`. Layer colour is
the element's CPK colour.
**Units:** core works in mm. The adapter scales to the document's units.

## 7. Puzzle rules

- **Joint position:** the midpoint of the bond.
- **Gender:** the half-bond of the heavier element (by atomic mass) gets the **hole**. If the masses
  are equal, the atom with the lower index gets the hole. As a result, H and halogen ends always
  carry pegs.
- **Profiles (rotation-honest):**

  | Bond | Profile | Why |
  |---|---|---|
  | Single | `ROUND`, `peg_radius` | spins freely, like a real σ bond |
  | Double | `D_FLAT` (one flat) | locked, and fits only one way, like a planar π bond |
  | Aromatic | `DOUBLE_FLAT` (two parallel flats) | locked, and fits two symmetric ways |
  | Triple | `ROUND`, `triple_peg_radius` (thicker) | linear, so rotation doesn't matter, and it is visibly different from single |

- **Key reference:** for `D_FLAT` and `DOUBLE_FLAT`, the normal of the flat follows the π
  direction: the normal of the plane through the bond's two atoms and one neighbour of either atom.
  If neither atom has another neighbour, a fixed perpendicular is used. It is computed **once per
  bond** and used by both halves, so the peg and hole always line up.
- **Hole size:** the hole's profile is the peg's profile offset outward by `clearance`. Hole depth
  is `peg_length + hole_extra_depth`, and the hole may extend into the ball.
- **Snap ridge** (experiment, after the first water print loosened with use): every peg has a
  0.4 mm band, raised by `ridge_height`, centred 1.5 mm from its tip, with 45° ramps. The hole
  has a groove of exactly the ridge's size at the same place. The ridge is wider than the hole
  bore by `ridge_height − clearance`, so it clicks in and holds. The wall check uses the groove.
- **Aromaticity:** by default, RDKit's aromaticity perception marks ring bonds as aromatic.
  The `Kekulize` import option turns them back into alternating single and double bonds. It is
  applied while reading the SDF, so it is not a stored parameter.
- **Validation:** `puzzle.check(pieces, params)` returns a tuple of `Issue(atom_index, message)`
  for:
  - wall thickness `stick_radius − (peg_radius + clearance) < min_wall` around a hole;
  - a joint (bond midpoint) inside its own ball;
  - any two balls overlapping, bonded or not;
  - a hole reaching past the ball's centre.

  Every issue would give a broken print, so there are no warnings: any issue stops piece
  generation. (A peg can't be longer than its hole: hole depth is peg length plus
  `hole_extra_depth` by construction.)

## 8. Default parameters

| Parameter | FDM (default) | Resin |
|---|---|---|
| `scale_mm_per_a` | 20.0 | 12.0 |
| `ball_radius_factor` (× vdW radius) | 0.25 | 0.25 |
| `stick_radius_mm` | 3.5 | 2.2 |
| `peg_radius_mm` | 1.75 | 1.1 |
| `triple_peg_radius_mm` | 2.1 | 1.35 |
| `flat_depth_mm` (flat cut from the radius) | 0.6 | 0.4 |
| `peg_length_mm` | 5.0 | 3.5 |
| `hole_extra_depth_mm` | 0.4 | 0.3 |
| `clearance_mm` (radial) | 0.20 | 0.10 |
| `chamfer_mm` (peg lead-in) | 0.3 | 0.2 |
| `ridge_height_mm` (snap ridge, radial) | 0.3 | 0.15 |
| `min_wall_mm` | 1.0 | 0.6 |
| `include_hydrogens` | true | true |

Sanity check with FDM settings on a C–H bond: 21.8 mm between centres, C ball 8.5 mm, H ball 6.0 mm.
The joint is 2.4 mm outside the C ball. The hole goes 5.4 mm deep, ending 5.5 mm from C's centre,
which is inside the ball. Triple-bond wall at the groove: 3.5 − 2.4 = 1.1 mm ≥ 1.0. These defaults should be
**adjusted after the first test prints** (M9).

## 9. Error handling

All of these subclass `MolkitError`, and commands catch `MolkitError` to show a readable message:

- `UnknownElementError`: symbol not in the element table
- `SdfParseError`: unreadable SDF, or a bond type with no peg shape (dative, "any")
- `CompoundNotFoundError`
- `No3DConformerError`
- `NetworkError`
- `CifParseError`: unreadable CIF, or no data block with atom sites
- `NoMoleculeFoundError`: no discrete molecule in the crystal (a polymer or framework)

Not errors: guessed (all-single) bond orders and missing hydrogens come back as notes from
`parse_cif` for the command to print.
- `ModelDataError`: stored model JSON is corrupt or from an unsupported schema version

PubChem's usage policy allows up to 5 requests per second. molkit makes one request per command, so
it needs no throttling. Requests send a User-Agent that identifies molkit and time out after 30 s.
PubChem answers 404 both for unknown names ("No CID found") and for compounds with no 3D record.
The message body tells them apart.

## 10. Milestones (build order)

Each milestone is a small vertical slice. **Definition of done:** ruff, mypy, and pytest all pass,
core coverage stays at 100%, the README is updated if anything user-visible changed, and the work is
committed.

| # | Slice | Tests / proof |
|---|---|---|
| M0 | Scaffold: `pyproject.toml`, ruff, mypy, pytest + coverage, CI on Py 3.9, empty packages, `test_architecture.py`. **Check that `rdkit` and `gemmi` install in Rhino 8 CPython, and pin the versions.** | CI green. Architecture test fails on a planted `import Rhino`. |
| M1 | `vec`, `elements`, `model` (`neighbors`), `errors`. | Unit tests for vector math, element data sanity, neighbours. |
| M2 | `sdf.parse` (RDKit, keeps Hs, aromatic/kekule modes) using fixture SDFs. | Methane has 5 atoms and 4 single bonds, with H–C–H angles of 109.5° ± 1°. Benzene aromatic gives 6 aromatic C–C bonds, kekule gives 3+3. |
| M3 | `pubchem.fetch_sdf` with an injected HTTP function and error mapping. | Fake transport for 200 / 404 / no-3D / timeout. No real network in tests. |
| M4 | `params` + presets, and `serialize` round-trip for `PuzzleModel`. | Round-trip equality. Unknown schema version and corrupt data raise. |
| M5 | `ballstick.build`. | Ball radii and colours; sticks end at the midpoints; the H toggle works. |
| M6 | **First Rhino slice:** `rhino/draw.py` (layers, unit scaling, ball blocks, sticks), `rhino/storage.py`, `core/info.py` (formula + summary), and the `MolkitFetch` and `MolkitInfo` commands. | Manual smoke checklist in `docs/smoke-test.md`: methane appears with the right layers and colours, and `MolkitInfo` reads the anchor. |
| M7 | `MolkitSettings` + `MolkitRegenerate`. Core: `PRESETS`, `with_preset`, `option_name`. | Core: preset keeps hydrogens; every param gets a distinct valid Rhino option name. Smoke test: change the scale and the model rebuilds. |
| M8 | Puzzle core: `puzzle.py` (`build_pieces`, `check`), sharing `visible_atoms` and `ball_radius` with `ballstick.py`. | Gender rule incl. ties; key_ref ⟂ direction and identical on both halves; ethylene → D_FLAT, benzene → DOUBLE_FLAT, acetylene → thick ROUND; validation catches thin walls and overlaps. |
| M9 | Rhino puzzle geometry + `MolkitPuzzle`. **Test-print** methane first, then ethylene and benzene (FDM), then tune the defaults. | Smoke test: every piece is a closed, valid solid. Print notes are recorded in `docs/print-tests.md`. |
| M10 | `stl.binary_stl` + `manifest` (file names, assembly JSON), `rhino/export`, `MolkitExportStl`. STL meshes use a fixed 0.02 mm max deviation for every preset (a per-preset parameter would invalidate stored models). | Core: binary STL header, triangle count, and byte layout; manifest content. Smoke test: files open in a slicer. |
| M10b | 3D fallback: when PubChem has no 3D record (e.g. > 50 heavy atoms, like α-cyclodextrin), fetch the 2D SDF and generate coordinates with RDKit (add H, ETKDGv3 with macrocycle torsions, MMFF cleanup). The source records that coordinates were computed, and `MolkitInfo` shows it; error messages explain PubChem's limits. | Core: fake transport serving 2D → 3D molecule with sensible bond lengths; generation failure raises. Smoke test: α-cyclodextrin builds as ball-and-stick. |
| M11 | `cif.parse_cif`: gemmi reads the first block with atom sites and expands it to the unit cell; disorder groups 0 and 1 are kept; a 3×3×3 block of cells is split into molecules by RDKit connectivity; the largest molecule whose centroid lies in the home cell is kept (a fragment bigger than the cell's site count means a polymer or framework → `NoMoleculeFoundError`); RDKit assigns bond orders, falling back to single bonds. Returns `(Molecule, notes)`; notes cover guessed bond orders and missing hydrogens. | Real fixture: aspirin (COD 2104857, P2₁/c, Z = 4): C9H8O4, 21 bonds, 6 aromatic + 2 C=O. Hand-made fixtures: methane split across the cell edge, disordered H, CO2 without H, an endless carbon chain, Fe, garbage and block without atom sites. |
| M12 | `MolkitImportCif`: file dialog → `parse_cif` → same model as `MolkitFetch`; notes are printed. No `Kekulize` option yet (add it if CIF users ask). | Smoke test with the fixture CIFs. |
| M13 | Packaging: `rhino/molkit.rhproj` created and built in the Script Editor (commands + `src/molkit` library → `.rhp` + `.yak`), steps in `docs/packaging.md`; install the build with the dev `.pth` disabled; README with the puzzle rules, presets, limitations and a Mermaid architecture diagram; MIT license; tag `v0.1.1-beta` with the `.yak` (Script Editor rejected `0.1.0`) on a GitHub release. Screenshots, a GIF and a print photo come once there are real prints. | Built plugin passes the full smoke test. |

## 11. Post-MVP ideas

- Ring-closure joints: detect one closure bond per ring and give it a short, chamfered, extra-clearance
  snap peg.
- Engraved atom labels and flat print bases.
- Magnet pockets as an alternative joint style.
- Cluster or unit-cell cutting for extended structures.
- Grasshopper components.

## 12. Open items

- License: **MIT** ([LICENSE](LICENSE)).
- Confirmed 2026-10-11: the pinned `rdkit`/`gemmi` install and run inside Rhino 8.35 (CPython
  3.9.10, Windows) via `# r:` requirements. Rhino's pip uses a 15 s timeout, so the first install
  (~40 MB with numpy) can time out on a slow connection. Re-running works, and the README must
  say so. macOS is still unverified.
