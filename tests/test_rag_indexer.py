import pytest
import asyncio
from unittest.mock import MagicMock, patch
from app.rag.indexer import index_all_documents


@pytest.mark.asyncio
async def test_indexer_empty_folder(tmp_path, monkeypatch):
    # Point KB_DIR to an empty temp folder
    monkeypatch.setattr("app.rag.indexer.KB_DIR", tmp_path)
    # Mock ChromaDB client
    mock_client = MagicMock()
    monkeypatch.setattr("app.rag.indexer.get_chroma_client", lambda: mock_client)

    stats = await index_all_documents()
    assert stats["indexed"] == 0
    assert stats["skipped"] == 0


@pytest.mark.asyncio
async def test_indexer_with_files(tmp_path, monkeypatch):
    # 1. Setup temp environment
    monkeypatch.setattr("app.rag.indexer.KB_DIR", tmp_path)

    # Create a fake PDF
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"Fake PDF content")

    # 2. Mock external dependencies
    # Mock fitz.open
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = (
        "This is a test document content for RAG indexing. " * 10
    )
    mock_doc.__iter__.return_value = [mock_page]
    mock_doc.close = MagicMock()

    with patch("fitz.open", return_value=mock_doc):
        # Mock ChromaDB
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"metadatas": []}
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        monkeypatch.setattr("app.rag.indexer.get_chroma_client", lambda: mock_client)

        # Mock Embeddings
        async def mock_get_batch(texts):
            return [[0.1] * 768 for _ in texts]

        monkeypatch.setattr("app.rag.indexer.get_embeddings_batch", mock_get_batch)

        # 3. Run Indexer
        stats = await index_all_documents()

        # 4. Assertions
        assert stats["indexed"] > 0
        assert mock_collection.upsert.called
        # Check metadata
        call_args = mock_collection.upsert.call_args[1]
        assert call_args["metadatas"][0]["source_file"] == "test.pdf"


if __name__ == "__main__":
    asyncio.run(test_indexer_with_files())
