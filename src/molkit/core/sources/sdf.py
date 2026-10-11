"""SDF/MOL record -> Molecule, via RDKit."""

from __future__ import annotations

from rdkit import Chem

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


def parse_sdf(text: str, source: SourceInfo, kekulize: bool = False) -> Molecule:
    """Read the first record of an SDF, keeping explicit hydrogens.

    RDKit perceives aromaticity while sanitizing; `kekulize` turns aromatic rings back into
    alternating single/double bonds.
    """
    mol = Chem.MolFromMolBlock(text, removeHs=False)
    if mol is None:
        raise SdfParseError(f"could not read SDF for {source.identifier!r}")
    if not mol.GetConformer().Is3D():
        raise No3DConformerError(f"{source.identifier!r} has only 2D coordinates")
    if kekulize:
        Chem.Kekulize(mol, clearAromaticFlags=True)
    return Molecule(source.identifier, _atoms(mol), _bonds(mol), source)


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
