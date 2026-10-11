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

Fetch = Callable[[str], bytes]

_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/SDF?record_type=3d"
_TIMEOUT_S = 30


def http_get(url: str) -> bytes:
    """GET `url`; PubChem's usage policy asks clients to identify themselves."""
    request = Request(url, headers={"User-Agent": "molkit (Rhino 8 molecular puzzle plugin)"})
    with urlopen(request, timeout=_TIMEOUT_S) as response:
        body: bytes = response.read()
    return body


def fetch_sdf(name: str, fetch: Fetch = http_get) -> str:
    """Download the 3D conformer SDF for a compound name."""
    try:
        return fetch(_URL.format(quote(name.strip(), safe=""))).decode()
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
    return No3DConformerError(f"PubChem has no 3D structure for {name!r}")
