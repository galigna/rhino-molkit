"""CIF of a molecular crystal -> one complete Molecule, via gemmi (symmetry) and RDKit (bonds).

Expands the asymmetric unit to the whole unit cell, builds a 3x3x3 block of cells so molecules
cut by the cell edges are whole somewhere, splits it into molecules by connectivity, and keeps
the one copy whose centre lies in the original cell.
"""

from __future__ import annotations

import itertools
import math
from pathlib import Path

import gemmi
from rdkit import Chem
from rdkit.Chem import rdDetermineBonds

from molkit.core.elements import element
from molkit.core.errors import CifParseError, NoMoleculeFoundError
from molkit.core.model import Molecule, SourceInfo
from molkit.core.sources.sdf import molecule_from_rdkit

Image = tuple[str, gemmi.Position]  # element symbol, Cartesian position (Å)

# Disorder group 0 is ordered; 1 is the first alternative. Higher groups are other alternatives.
_KEPT_DISORDER_GROUPS = (0, 1)
# A centroid exactly on a cell face belongs to the cell on its positive side, never to both.
_FACE_TOLERANCE = 1e-6


def parse_cif(
    text: str, source: SourceInfo, kekulize: bool = False
) -> tuple[Molecule, tuple[str, ...]]:
    """One complete molecule from the first data block with atom sites, plus notes for the user
    (missing hydrogens, guessed bond orders). Polymers and frameworks raise."""
    structure = _read(text, source)
    sites = [
        s for s in structure.get_all_unit_cell_sites() if s.disorder_group in _KEPT_DISORDER_GROUPS
    ]
    for site in sites:
        element(site.element.name)  # RDKit's bond perception crashes on unknown elements
    images = _images(structure.cell, sites)
    fragment = _home_fragment(images, structure.cell, len(sites), source)
    mol, notes = _with_bonds([images[i] for i in fragment], kekulize)
    if not any(symbol == "H" for symbol, _ in images):
        notes += ("the file has no hydrogen positions, so the model has none",)
    return molecule_from_rdkit(mol, Path(source.identifier).stem, source), notes


def _read(text: str, source: SourceInfo) -> gemmi.SmallStructure:
    try:
        blocks = [b for b in gemmi.cif.read_string(text) if b.find_values("_atom_site_fract_x")]
    except (RuntimeError, ValueError) as error:
        raise CifParseError(f"could not read CIF {source.identifier!r}: {error}") from None
    if not blocks:
        raise CifParseError(f"CIF {source.identifier!r} has no atom sites")
    return gemmi.make_small_structure_from_block(blocks[0])


def _images(cell: gemmi.UnitCell, sites: list[gemmi.SmallStructure.Site]) -> list[Image]:
    shifts = list(itertools.product((-1, 0, 1), repeat=3))
    return [
        (
            s.element.name,
            cell.orthogonalize(gemmi.Fractional(*(f + d for f, d in zip(s.fract.tolist(), shift)))),
        )
        for shift in shifts
        for s in sites
    ]


def _home_fragment(
    images: list[Image], cell: gemmi.UnitCell, sites_per_cell: int, source: SourceInfo
) -> tuple[int, ...]:
    mol = _xyz_mol(images)
    rdDetermineBonds.DetermineConnectivity(mol)
    # A molecule can't have more atoms than the cell has sites; anything bigger is a network.
    candidates = [
        fragment
        for fragment in Chem.GetMolFrags(mol)
        if len(fragment) <= sites_per_cell and _in_home_cell(fragment, images, cell)
    ]
    if not candidates:
        raise NoMoleculeFoundError(
            f"{source.identifier!r} has no discrete molecule (a polymer or framework?)"
        )
    return max(candidates, key=len)  # the main molecule rather than solvent or counter-ions


def _in_home_cell(fragment: tuple[int, ...], images: list[Image], cell: gemmi.UnitCell) -> bool:
    n = len(fragment)
    x, y, z = (sum(getattr(images[i][1], axis) for i in fragment) / n for axis in "xyz")
    centre = cell.fractionalize(gemmi.Position(x, y, z))
    return all(math.floor(c + _FACE_TOLERANCE) == 0 for c in centre.tolist())


def _with_bonds(images: list[Image], kekulize: bool) -> tuple[Chem.Mol, tuple[str, ...]]:
    mol = _xyz_mol(images)
    rdDetermineBonds.DetermineConnectivity(mol)
    ordered = Chem.Mol(mol)
    try:
        rdDetermineBonds.DetermineBondOrders(ordered, charge=0)
    except (ValueError, RuntimeError, IndexError):  # IndexError: RDKit has no rules for metals
        return mol, ("bond orders could not be determined, so every bond is single",)
    if kekulize:
        Chem.Kekulize(ordered, clearAromaticFlags=True)
    return ordered, ()


def _xyz_mol(images: list[Image]) -> Chem.Mol:
    lines = [f"{symbol} {p.x:.6f} {p.y:.6f} {p.z:.6f}" for symbol, p in images]
    return Chem.MolFromXYZBlock(f"{len(lines)}\n\n" + "\n".join(lines))
