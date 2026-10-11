"""SDF/MOL record -> Molecule, via RDKit."""

from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import AllChem

from molkit.core.elements import element
from molkit.core.errors import No3DConformerError, SdfParseError
from molkit.core.model import Atom, Bond, BondOrder, Molecule, SourceInfo
from molkit.core.vec import Vec3

_BOND_ORDERS: dict[Chem.BondType, BondOrder] = {
    Chem.BondType.SINGLE: BondOrder.SINGLE,
    Chem.BondType.DOUBLE: BondOrder.DOUBLE,
    Chem.BondType.TRIPLE: BondOrder.TRIPLE,
    Chem.BondType.AROMATIC: BondOrder.AROMATIC,
}


# Fixed seed: the same molecule always gets the same generated coordinates.
_EMBED_SEED = 0x6D6B


def parse_sdf(
    text: str, source: SourceInfo, kekulize: bool = False, generate_3d: bool = False
) -> Molecule:
    """Read the first record of an SDF, keeping explicit hydrogens.

    RDKit perceives aromaticity while sanitizing; `kekulize` turns aromatic rings back into
    alternating single/double bonds. A 2D record raises unless `generate_3d` is set.
    """
    mol = Chem.MolFromMolBlock(text, removeHs=False)
    if mol is None:
        raise SdfParseError(f"could not read SDF for {source.identifier!r}")
    if not mol.GetConformer().Is3D():
        if not generate_3d:
            raise No3DConformerError(f"{source.identifier!r} has only 2D coordinates")
        mol = _generate_3d(mol, source)
    if kekulize:
        Chem.Kekulize(mol, clearAromaticFlags=True)
    return molecule_from_rdkit(mol, source.identifier, source)


def _generate_3d(mol: Chem.Mol, source: SourceInfo) -> Chem.Mol:
    """ETKDGv3 (knows macrocycle torsions) for the shape, then an MMFF clean-up of bond lengths."""
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = _EMBED_SEED
    if AllChem.EmbedMolecule(mol, params) != 0:
        raise No3DConformerError(
            f"RDKit could not generate 3D coordinates for {source.identifier!r}"
        )
    AllChem.MMFFOptimizeMolecule(mol, maxIters=2000)
    return mol


def molecule_from_rdkit(mol: Chem.Mol, name: str, source: SourceInfo) -> Molecule:
    """A Molecule from an RDKit molecule with a 3D conformer; validates elements and bond types."""
    return Molecule(name, _atoms(mol), _bonds(mol), source)


def _atoms(mol: Chem.Mol) -> tuple[Atom, ...]:
    positions = mol.GetConformer().GetPositions()
    return tuple(
        Atom(element(atom.GetSymbol()).symbol, Vec3(*(float(c) for c in xyz)))
        for atom, xyz in zip(mol.GetAtoms(), positions)
    )


def _bonds(mol: Chem.Mol) -> tuple[Bond, ...]:
    try:
        return tuple(
            Bond(b.GetBeginAtomIdx(), b.GetEndAtomIdx(), _BOND_ORDERS[b.GetBondType()])
            for b in mol.GetBonds()
        )
    except KeyError as missing:
        raise SdfParseError(f"unsupported bond type: {missing.args[0]}") from None
