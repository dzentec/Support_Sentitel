import pytest
import asyncio
from unittest.mock import MagicMock, patch
from app.rag.retriever import retrieve


@pytest.mark.asyncio
async def test_retrieve_success(monkeypatch):
    # 1. Mock dependencies
    # Mock embedding
    async def mock_get_emb(text):
        return [0.1] * 768

    monkeypatch.setattr("app.rag.retriever.get_embedding", mock_get_emb)

    # Mock ChromaDB Collection
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["Relevant text content"]],
        "metadatas": [[{"source_file": "doc.pdf", "page": 1}]],
        "distances": [[0.1]],  # 1.0 - 0.1 = 0.9 similarity
    }
    monkeypatch.setattr(
        "app.rag.retriever.get_chroma_collection", lambda: mock_collection
    )

    # 2. Run Retrieve
    ctx = await retrieve("test query")

    # 3. Assertions
    assert not ctx.is_empty
    assert len(ctx.chunks) == 1
    assert ctx.chunks[0].text == "Relevant text content"
    assert ctx.chunks[0].score == 0.9


@pytest.mark.asyncio
async def test_retrieve_below_threshold(monkeypatch):
    # Mock dependencies
    async def mock_get_emb(text):
        return [0.1] * 768

    monkeypatch.setattr("app.rag.retriever.get_embedding", mock_get_emb)

    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["Irrelevant text"]],
        "metadatas": [[{"source_file": "doc.pdf", "page": 1}]],
        "distances": [[0.8]],  # 1.0 - 0.8 = 0.2 similarity < 0.75
    }
    monkeypatch.setattr(
        "app.rag.retriever.get_chroma_collection", lambda: mock_collection
    )

    # Run Retrieve
    ctx = await retrieve("test query")

    # Assertions
    assert ctx.is_empty
    assert len(ctx.chunks) == 0


if __name__ == "__main__":
    asyncio.run(test_retrieve_success())
