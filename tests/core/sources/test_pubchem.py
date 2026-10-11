from __future__ import annotations

import io
import socket
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from molkit.core.errors import CompoundNotFoundError, NetworkError, No3DConformerError
from molkit.core.model import SourceInfo
from molkit.core.sources import pubchem
from molkit.core.sources.pubchem import fetch_sdf
from molkit.core.sources.sdf import parse_sdf

METHANE_SDF = (Path(__file__).parents[2] / "fixtures" / "methane.sdf").read_bytes()

# Bodies PubChem actually returns with its 404s (checked 2026-10-11).
NO_CID = b"Status: 404\nCode: PUGREST.NotFound\nMessage: No CID found\n"
NO_3D = b"Status: 404\nCode: PUGREST.NotFound\nMessage: No records found for the given CID(s)\n"


def _http_error(code: int, body: bytes = b""):
    def fetch(url: str) -> bytes:
        raise HTTPError(url, code, "error", None, io.BytesIO(body))  # type: ignore[arg-type]

    return fetch


def _raising(error: Exception):
    def fetch(url: str) -> bytes:
        raise error

    return fetch


def test_fetches_3d_record_that_parses_to_methane() -> None:
    urls = []

    def fake(url: str) -> bytes:
        urls.append(url)
        return METHANE_SDF

    text = fetch_sdf("methane", fake)
    assert urls == [
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/methane/SDF?record_type=3d"
    ]
    assert len(parse_sdf(text, SourceInfo("pubchem", "methane")).atoms) == 5


def test_name_is_trimmed_and_url_escaped() -> None:
    urls = []
    fetch_sdf("  acetic acid/2 ", lambda url: urls.append(url) or METHANE_SDF)
    assert "/name/acetic%20acid%2F2/SDF" in urls[0]


def test_unknown_name_raises_compound_not_found() -> None:
    with pytest.raises(CompoundNotFoundError, match="notacompound"):
        fetch_sdf("notacompound", _http_error(404, NO_CID))


def test_compound_without_3d_record_raises() -> None:
    with pytest.raises(No3DConformerError, match="insulin"):
        fetch_sdf("insulin", _http_error(404, NO_3D))


def test_other_http_error_raises_network_error() -> None:
    with pytest.raises(NetworkError, match="503"):
        fetch_sdf("methane", _http_error(503))


@pytest.mark.parametrize("error", [URLError("offline"), socket.timeout("timed out")])
def test_connection_problem_raises_network_error(error: Exception) -> None:
    with pytest.raises(NetworkError, match="PubChem"):
        fetch_sdf("methane", _raising(error))


def test_default_transport_identifies_itself_and_times_out(monkeypatch) -> None:
    seen = {}

    def fake_urlopen(request, timeout):
        seen["agent"] = request.get_header("User-agent")
        seen["timeout"] = timeout
        return io.BytesIO(b"sdf")

    monkeypatch.setattr(pubchem, "urlopen", fake_urlopen)
    assert pubchem.http_get("https://example.test") == b"sdf"
    assert seen["agent"].startswith("molkit")
    assert seen["timeout"] > 0
