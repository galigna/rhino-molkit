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
- Generating 3D coordinates for compounds that have no PubChem 3D record (we raise a clear error).
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
│  │  ├─ params.py           # ModelParams, PuzzleParams, presets
│  │  ├─ serialize.py        # JSON round-trip with schema version
│  │  ├─ errors.py           # MolkitError hierarchy
│  │  ├─ sources/
│  │  │  ├─ sdf.py           # SDF/MOL block -> Molecule (RDKit)
│  │  │  ├─ pubchem.py       # PUG REST client (injectable HTTP)
│  │  │  └─ cif.py           # CIF -> Molecule (gemmi + RDKit)
│  │  ├─ ballstick.py        # Molecule + ModelParams -> BallStickSpec
│  │  ├─ puzzle/
│  │  │  ├─ gender.py        # which end of a bond gets the peg
│  │  │  ├─ keying.py        # shared key-reference vector per bond
│  │  │  ├─ profiles.py      # bond order -> PegProfile
│  │  │  ├─ pieces.py        # Molecule + params -> tuple[PieceSpec]
│  │  │  └─ validate.py      # printability checks (wall, overlap, depth)
│  │  ├─ manifest.py         # assembly manifest
│  │  └─ stl.py              # triangles -> binary STL bytes
│  └─ rhino/                 # thin adapter: specs -> Rhino geometry
│     ├─ units.py            # doc-unit scaling
│     ├─ layers.py
│     ├─ blocks.py           # one block definition per element/radius
│     ├─ geometry.py         # BallStickSpec / PieceSpec -> Brep/Mesh
│     ├─ storage.py          # anchor object + user dictionary I/O
│     ├─ export.py           # Mesh -> triangles -> core.stl
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
CIF  ─► cif.parse ──────────────────────┴─► Molecule ─┬─► ballstick.build ─► BallStickSpec ─► rhino.geometry
                                                      └─► puzzle.build ────► PieceSpec[] ───► rhino.geometry ─► rhino.export ─► stl.write
```

**Boundary rule:** `core` returns plain frozen dataclasses that hold every number the geometry
needs: centres, radii, directions, lengths, and profile dimensions. `rhino` only turns those specs
into Rhino objects. It makes **no chemistry or puzzle decisions**, so all of the logic stays
testable without Rhino.

**Runtime:** Rhino 8 runs CPython **3.9**, so all code targets 3.9. `rdkit` and `gemmi` are **hard
dependencies**, declared as Script Editor package requirements and pinned to versions that ship
cp39 wheels for Windows and macOS (pinned in M0).

## 5. Data model (core)

All of these are `@dataclass(frozen=True)`. Collections are `tuple`s. Coordinates are in **Å** in
the molecule and in **mm** in the specs.

```python
class BondOrder(Enum): SINGLE, DOUBLE, TRIPLE, AROMATIC

Vec3(x: float, y: float, z: float)                  # +, -, *, dot, cross, norm, unit

Element(symbol, atomic_number, mass, covalent_radius, vdw_radius, color_rgb)

Atom(element: str, position: Vec3)                  # element: canonical symbol, e.g. "Cl"
Bond(a: int, b: int, order: BondOrder)              # indices into Molecule.atoms, either order
SourceInfo(kind: Literal["pubchem", "cif"], identifier: str)
Molecule(name: str, atoms: tuple[Atom, ...], bonds: tuple[Bond, ...], source: SourceInfo)
    .without_hydrogens() -> Molecule                # reindexes atoms and bonds
    .neighbors(i) -> tuple[int, ...]

ModelParams(scale_mm_per_a, ball_radius_factor, stick_radius_mm, include_hydrogens, aromatic_mode)
PuzzleParams(preset_name, clearance_mm, peg_length_mm, hole_extra_depth_mm, peg_radius_mm,
             triple_peg_radius_mm, flat_depth_mm, chamfer_mm, min_wall_mm)

BallSpec(atom_index, center: Vec3, radius, color_rgb, element)
StickSpec(atom_index, bond_index, start: Vec3, end: Vec3, radius, color_rgb)   # half-bond
BallStickSpec(balls: tuple[BallSpec, ...], sticks: tuple[StickSpec, ...])

class Gender(Enum): PEG, HOLE
class ProfileKind(Enum): ROUND, D_FLAT, DOUBLE_FLAT
PegProfile(kind, radius, flat_depth)                # flat_depth unused for ROUND
Joint(bond_index, partner_atom, direction: Vec3,    # unit vector, piece centre -> partner
      key_ref: Vec3,                                # unit, ⟂ direction; shared by both halves
      stub_length, gender, profile, peg_length, hole_depth, clearance)
PieceSpec(atom_index, element, center, ball_radius, stick_radius, color_rgb, joints: tuple[Joint, ...])

PuzzleModel(model_id: str, molecule: Molecule, model_params: ModelParams,
            puzzle_params: PuzzleParams, schema_version: int)   # what is persisted
```

**Persistence:** `serialize.dumps(PuzzleModel) -> str` and `serialize.loads(str) -> PuzzleModel`
write JSON that includes `schema_version`. Unknown versions raise `SchemaVersionError`.

**Storage in Rhino:** each model gets one locked **anchor** object (a point at the molecule's
centroid on `Molkit::<name>::_data`). It holds the serialized `PuzzleModel` in its UserDictionary
under `molkit.model`. Every generated object carries the user strings `molkit.model_id`,
`molkit.role` (`ball|stick|piece`), and `molkit.atom_index`. Copying the anchor between files
copies the model. Regenerating deletes everything with that `model_id` except the anchor, then
rebuilds.

## 6. Commands

| Command | Does |
|---|---|
| `MolkitFetch` | Asks for a compound name, fetches the PubChem 3D SDF, and builds the ball-and-stick model plus its anchor. |
| `MolkitImportCif` | Picks a `.cif` file, extracts one molecule, and builds the ball-and-stick model plus its anchor. |
| `MolkitPuzzle` | Picks a model's anchor or any object in the model, then builds the puzzle pieces on `Molkit::<name>::Pieces`. Printability warnings are printed to the command line. |
| `MolkitSettings` | Picks a model and edits its parameters (preset, clearance, hydrogens, scale, …) with command-line options. Saves to the anchor and regenerates. |
| `MolkitRegenerate` | Picks a model and rebuilds all of its geometry from the anchor data. |
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
- **Aromaticity:** `aromatic_mode = "aromatic"` (the default) runs RDKit aromaticity perception.
  `"kekule"` keeps alternating single and double bonds.
- **Validation** (`validate.py`) returns a tuple of `Issue(severity, atom_index, message)` for:
  - wall thickness `stick_radius − (peg_radius + clearance) < min_wall`;
  - neighbouring balls overlapping;
  - a hole reaching past the ball's centre;
  - a peg longer than the partner's available depth.

  Errors stop piece generation. Warnings are printed.

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
| `min_wall_mm` | 1.0 | 0.6 |
| `include_hydrogens` | true | true |
| `aromatic_mode` | `"aromatic"` | `"aromatic"` |
| STL mesh: max deviation | 0.05 mm | 0.02 mm |

Sanity check with FDM settings on a C–H bond: 21.8 mm between centres, C ball 8.5 mm, H ball 6.0 mm.
The joint is 2.4 mm outside the C ball. The hole goes 5.4 mm deep, ending 5.5 mm from C's centre,
which is inside the ball. Triple-bond wall: 3.5 − 2.3 = 1.2 mm ≥ 1.0. These defaults should be
**adjusted after the first test prints** (M9).

## 9. Error handling

All of these subclass `MolkitError`, and commands catch `MolkitError` to show a readable message:

- `UnknownElementError`: symbol not in the element table
- `CompoundNotFoundError`
- `No3DConformerError`
- `NetworkError`
- `CifParseError`
- `NoMoleculeFoundError`
- `BondPerceptionWarning` (bond orders are set to single when RDKit can't assign them)
- `SchemaVersionError`
- `PrintabilityError`

Following PubChem's usage policy, requests are throttled to at most 5 per second and send a
User-Agent that identifies molkit.

## 10. Milestones (build order)

Each milestone is a small vertical slice. **Definition of done:** ruff, mypy, and pytest all pass,
core coverage stays at 100%, the README is updated if anything user-visible changed, and the work is
committed.

| # | Slice | Tests / proof |
|---|---|---|
| M0 | Scaffold: `pyproject.toml`, ruff, mypy, pytest + coverage, CI on Py 3.9, empty packages, `test_architecture.py`. **Check that `rdkit` and `gemmi` install in Rhino 8 CPython, and pin the versions.** | CI green. Architecture test fails on a planted `import Rhino`. |
| M1 | `vec`, `elements`, `model` (validation, `without_hydrogens`, `neighbors`), `errors`. | Unit tests for vector math, invariants, H removal and reindexing. |
| M2 | `sdf.parse` (RDKit, keeps Hs, aromatic/kekule modes) using fixture SDFs. | Methane has 5 atoms and 4 single bonds, with H–C–H angles of 109.5° ± 1°. Benzene aromatic gives 6 aromatic C–C bonds, kekule gives 3+3. |
| M3 | `pubchem.fetch_sdf` with an injected HTTP function, throttling, and error mapping. | Fake transport for 200 / 404 / no-3D / timeout. No real network in tests. |
| M4 | `params` + presets, and `serialize` round-trip for `PuzzleModel`. | Round-trip equality. Unknown schema version raises. |
| M5 | `ballstick.build`. | Ball radii and colours; sticks end at the midpoints; the H toggle works. |
| M6 | **First Rhino slice:** `units`, `layers`, `blocks`, `geometry` (ball-and-stick), `storage`, and the `MolkitFetch` and `MolkitInfo` commands. | Manual smoke checklist in `docs/smoke-test.md`: methane appears with the right layers and colours, and `MolkitInfo` reads the anchor. |
| M7 | `MolkitSettings` + `MolkitRegenerate`. | Core: parameter-update helpers are tested. Smoke test: change the scale and the model rebuilds. |
| M8 | Puzzle core: `gender`, `keying`, `profiles`, `pieces`, `validate`. | Gender rule incl. ties; key_ref ⟂ direction and identical on both halves; ethylene → D_FLAT, benzene → DOUBLE_FLAT, acetylene → thick ROUND; validation catches thin walls and overlaps. |
| M9 | Rhino puzzle geometry + `MolkitPuzzle`. **Test-print** methane first, then ethylene and benzene (FDM), then tune the defaults. | Smoke test: every piece is a closed, valid solid. Print notes are recorded in `docs/print-tests.md`. |
| M10 | `stl.write` + `manifest`, `rhino/export`, `MolkitExportStl`. | Core: binary STL header, triangle count, and byte layout; manifest content. Smoke test: files open in a slicer. |
| M11 | `cif.parse`: gemmi read, symmetry expansion, disorder (highest occupancy / altloc A), RDKit connectivity + bond orders, one-molecule extraction. | Fixtures: a small organic CIF (e.g. urea, aspirin) has the expected formula and bond count. A molecule split across cell edges comes out whole. Malformed CIF raises. |
| M12 | `MolkitImportCif`. | Smoke test with the fixture CIFs. |
| M13 | Packaging: `.rhproj`, Yak build, install on a clean Rhino 8; README with screenshots, a GIF, a printed photo, and an architecture diagram; tag `v0.1.0`. | Fresh install runs every command. |

## 11. Post-MVP ideas

- Ring-closure joints: detect one closure bond per ring and give it a short, chamfered, extra-clearance
  snap peg.
- RDKit ETKDG embedding when PubChem has no 3D record.
- Engraved atom labels and flat print bases.
- Magnet pockets as an alternative joint style.
- Cluster or unit-cell cutting for extended structures.
- Grasshopper components.

## 12. Open items

- License: assumed **MIT** unless changed.
- Exact `rdkit` and `gemmi` pins depend on M0 (newest releases with cp39 wheels on win-x64 and macOS).
