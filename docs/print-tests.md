# Print tests

The FDM and resin defaults in `src/molkit/core/params.py` (SPEC §8) are educated guesses until
real prints confirm them. Record each print here, and change the presets only on this evidence.

## Status: first print done, peg retention being tested

M9 shipped without test prints (deferred on 2026-10-11). The first print (water, FDM preset)
fit well, but the round pegs worked loose after about 5 assemblies. Two fixes are being tested
on separate branches (below). Peg sizes for double and aromatic bonds are still untested.

## What to print and check

1. **Methane** (1 C piece and 4 H pieces): do round pegs go in by hand, hold, and spin?
2. **Ethylene**: does the D-shaped C=C peg fit only one way, and lock rotation?
3. **Benzene**: do ring pegs fit two ways (180° apart), and does the ring close? Ring closure
   is a known limitation (SPEC §3).

For each, note: too tight / good / too loose, and whether pegs broke or layers split.

## Experiment: pegs that stay tight

A plain round peg holds only by friction, and the friction wears off. Each branch adds one
feature that holds the peg by shape instead:

| Branch | Feature | Setting (`MolkitSettings`) | FDM default |
|---|---|---|---|
| `experiment/peg-ridge` | A ring around each peg clicks into a groove inside the hole. | `RidgeHeight` | 0.3 mm |
| `experiment/hole-ribs` | Three thin ribs inside each hole squash a little when the peg goes in. | `RibHeight` | 0.3 mm |

Both settings are 0.1 mm more than the 0.2 mm clearance: that is how far the feature presses
into the plastic.

**Print** water (1 O piece and 2 H pieces) on the same printer, material and settings as the
first print, so only the joint changes. For each branch, print one set at the default and,
if there is time, one set 0.1 mm higher and one 0.1 mm lower.

**Test** each set:

1. Push one H piece into the O piece by hand. Note how it feels: *falls in*, *snug*, *click*,
   *hard*, or *does not go in*.
2. Hold the O piece with the H piece hanging down and shake it lightly. Does the H stay?
3. Pull it out and push it back in, counting. Every 5 times, repeat step 2.
4. Stop at 30 times, or when the H falls out in step 2, or when something breaks.
5. Write a row below: the count, how it felt at the start and at the end, and any damage
   (broken peg, split layers, white stress marks).

The winning branch becomes the default; the other is deleted.

## Results

| Date | Printer, material, nozzle | Preset and changes | Molecule | Fit | Notes |
|---|---|---|---|---|---|
| | | | | | |
