"""PubChem PUG REST client: compound name -> 3D SDF text."""

from __future__ import annotations

from typing import Callable
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from molkit.core.errors import (
    CompoundNotFoundError,
    MolkitError,
    NetworkError,
    No3DConformerError,
)
from molkit.core.model import Molecule, SourceInfo
from molkit.core.sources.sdf import parse_sdf

Fetch = Callable[[str], bytes]

_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/SDF"
_TIMEOUT_S = 30


def http_get(url: str) -> bytes:
    """GET `url`; PubChem's usage policy asks clients to identify themselves."""
    request = Request(url, headers={"User-Agent": "molkit (Rhino 8 molecular puzzle plugin)"})
    with urlopen(request, timeout=_TIMEOUT_S) as response:
        body: bytes = response.read()
    return body


def fetch_molecule(name: str, kekulize: bool = False, fetch: Fetch = http_get) -> Molecule:
    """PubChem's 3D record or, for compounds it has none for, its 2D record with RDKit-generated
    coordinates (flagged on the source)."""
    try:
        return parse_sdf(fetch_sdf(name, fetch), SourceInfo("pubchem", name), kekulize)
    except No3DConformerError:
        flat = fetch_sdf(name, fetch, three_d=False)
        source = SourceInfo("pubchem", name, generated_3d=True)
        return parse_sdf(flat, source, kekulize, generate_3d=True)


def fetch_sdf(name: str, fetch: Fetch = http_get, three_d: bool = True) -> str:
    """Download the SDF for a compound name: the 3D conformer, or the 2D record."""
    url = _URL.format(quote(name.strip(), safe="")) + ("?record_type=3d" if three_d else "")
    try:
        return fetch(url).decode()
    except HTTPError as error:
        raise _from_http_error(name, error) from None
    except OSError as error:  # URLError, socket.timeout, connection resets
        raise NetworkError(f"could not reach PubChem: {error}") from None


def _from_http_error(name: str, error: HTTPError) -> MolkitError:
    if error.code != 404:
        return NetworkError(f"PubChem answered HTTP {error.code} for {name!r}")
    # PubChem uses 404 for both cases; only the message tells them apart.
    if b"No CID found" in error.read():
        return CompoundNotFoundError(f"PubChem has no compound named {name!r}")
    # PubChem only computes conformers for small, fairly rigid molecules (<= 50 heavy atoms).
    return No3DConformerError(f"PubChem has no 3D structure for {name!r}")
