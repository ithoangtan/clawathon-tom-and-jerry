from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.adapters.embeddings import Embedder


@pytest.fixture
def embedder() -> Embedder:
    return Embedder("test-model", cache_dir="/tmp/hf-cache")


def test_dimension_loads_model_and_returns_size(embedder: Embedder) -> None:
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 384

    with patch.object(embedder, "_get_model", return_value=mock_model):
        assert embedder.dimension == 384
    mock_model.get_sentence_embedding_dimension.assert_called_once()


def test_encode_query_shape_and_prefix(embedder: Embedder) -> None:
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 4
    mock_model.encode.return_value = np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)

    with patch.object(embedder, "_get_model", return_value=mock_model):
        vec = embedder.encode_query("hello world")

    assert vec.shape == (4,)
    assert vec.dtype == np.float32
    mock_model.encode.assert_called_once()
    prefixed = mock_model.encode.call_args[0][0]
    assert prefixed == ["query: hello world"]


def test_encode_passages_shape(embedder: Embedder) -> None:
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 4
    mock_model.encode.return_value = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ],
        dtype=np.float32,
    )

    with patch.object(embedder, "_get_model", return_value=mock_model):
        matrix = embedder.encode_passages(["doc a", "doc b"])

    assert matrix.shape == (2, 4)
    assert matrix.dtype == np.float32
    prefixed = mock_model.encode.call_args[0][0]
    assert prefixed == ["passage: doc a", "passage: doc b"]


def test_encode_passages_empty_returns_zero_rows(embedder: Embedder) -> None:
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 384

    with patch.object(embedder, "_get_model", return_value=mock_model):
        matrix = embedder.encode_passages([])

    assert matrix.shape == (0, 384)
    assert matrix.dtype == np.float32
    mock_model.encode.assert_not_called()
