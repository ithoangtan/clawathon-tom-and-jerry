from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.adapters.embeddings import Embedder, _BGE_M3_DIM


@pytest.fixture
def embedder() -> Embedder:
    return Embedder("baai/bge-m3", base_url="http://maas/v1", api_key="test-key")


def _mock_response(vecs: list[list[float]]) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {
        "data": [{"index": i, "embedding": v} for i, v in enumerate(vecs)]
    }
    return resp


def test_dimension_is_bge_m3(embedder: Embedder) -> None:
    assert embedder.dimension == _BGE_M3_DIM


def test_encode_query_shape_and_normalized(embedder: Embedder) -> None:
    raw = [1.0, 0.0] + [0.0] * (_BGE_M3_DIM - 2)
    with patch("httpx.post", return_value=_mock_response([raw])) as mock_post:
        vec = embedder.encode_query("hello world")

    assert vec.shape == (_BGE_M3_DIM,)
    assert vec.dtype == np.float32
    assert abs(float(np.linalg.norm(vec)) - 1.0) < 1e-5
    payload = mock_post.call_args.kwargs["json"]
    assert payload["input"] == ["hello world"]
    assert payload["encoding_format"] == "dense"
    assert payload["model"] == "baai/bge-m3"


def test_encode_passages_shape_and_no_prefix(embedder: Embedder) -> None:
    vecs = [[1.0] + [0.0] * (_BGE_M3_DIM - 1), [0.0, 1.0] + [0.0] * (_BGE_M3_DIM - 2)]
    with patch("httpx.post", return_value=_mock_response(vecs)) as mock_post:
        matrix = embedder.encode_passages(["doc a", "doc b"])

    assert matrix.shape == (2, _BGE_M3_DIM)
    assert matrix.dtype == np.float32
    payload = mock_post.call_args.kwargs["json"]
    assert payload["input"] == ["doc a", "doc b"]


def test_encode_passages_empty_returns_zero_rows(embedder: Embedder) -> None:
    with patch("httpx.post") as mock_post:
        matrix = embedder.encode_passages([])

    assert matrix.shape == (0, _BGE_M3_DIM)
    assert matrix.dtype == np.float32
    mock_post.assert_not_called()
