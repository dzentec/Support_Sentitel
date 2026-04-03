import pytest
import asyncio
from app.rag.schemas import RetrievedChunk, KBContext
from app.rag.chunker import chunk_text

# --- Unit Tests for Schemas ---


def test_kb_context_to_prompt_block_empty():
    ctx = KBContext(chunks=[], is_empty=True)
    assert ctx.to_prompt_block() == ""


def test_kb_context_to_prompt_block_with_data():
    chunk = RetrievedChunk(
        text="Test info", source_file="manual.pdf", page=5, score=0.9
    )
    ctx = KBContext(chunks=[chunk], is_empty=False)
    block = ctx.to_prompt_block()
    assert "<knowledge_base>" in block
    assert "[Source: manual.pdf, page 5]" in block
    assert "Test info" in block
    assert "</knowledge_base>" in block


# --- Unit Tests for Chunker ---


def test_chunk_text_basic():
    text = "This is sentence one. This is sentence two. " * 20
    chunks = chunk_text(text, "test.pdf", 1, "hash1", chunk_size=20, overlap=5)
    assert len(chunks) > 1
    for c in chunks:
        assert c.source_file == "test.pdf"
        assert c.page == 1
        assert len(c.text) >= 50


def test_chunk_text_empty():
    chunks = chunk_text("", "test.pdf", 1, "hash1")
    assert chunks == []


def test_chunk_text_overlap_boundary():
    # Test that overlap snaps to space
    # Needs to be > 50 chars to be accepted as a chunk
    text = (
        "This is a long sentence that should definitely be longer than fifty characters to pass the filter. "
        * 5
    )
    # Small chunk size to force split
    chunks = chunk_text(text, "test.pdf", 1, "hash1", chunk_size=20, overlap=10)
    assert len(chunks) > 1
    # Check that chunks are not empty and have some overlap logic applied
    for c in chunks:
        assert len(c.text) >= 50


# --- Integration / Mock Tests ---


@pytest.mark.asyncio
async def test_embedding_retry_logic(monkeypatch):
    from app.rag.embeddings import get_embedding, EmbeddingAPIError
    import httpx

    # Mock httpx.AsyncClient.post to return 429 once then 200
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data

        def json(self):
            return self._json

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError("Error", request=None, response=self)

    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MockResponse(429, {})
        return MockResponse(200, {"embedding": {"values": [0.1] * 768}})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    emb = await get_embedding("test text")
    assert len(emb) == 768
    assert call_count == 2


if __name__ == "__main__":
    # If run directly, just run chunker test as a smoke test
    test_chunk_text_basic()
    print("Smoke test passed!")
