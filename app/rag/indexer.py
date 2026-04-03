import hashlib
import fitz  # pymupdf
from pathlib import Path
import chromadb
import structlog
import os
import asyncio
from typing import Optional

from app.rag.chunker import chunk_text
from app.rag.embeddings import get_embeddings_batch, EmbeddingAPIError
from app.rag.schemas import TextChunk
from app.config import settings

log = structlog.get_logger()

# Use absolute paths resolved from the file's parent to the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
KB_DIR = PROJECT_ROOT / "knowledge_base"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"
COLLECTION_NAME = "knowledge_base"

# Singleton-like shared resources
_chroma_client: Optional[chromadb.PersistentClient] = None
_indexing_lock = asyncio.Lock()


def get_chroma_client() -> chromadb.PersistentClient:
    """Get or create a shared ChromaDB PersistentClient."""
    global _chroma_client
    if _chroma_client is None:
        if not CHROMA_DIR.exists():
            CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _chroma_client


def get_chroma_collection() -> chromadb.Collection:
    """Get (or create) ChromaDB collection using the shared client."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def _file_hash(path: Path) -> str:
    """SHA-256 file hash for incremental indexing."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return f"sha256:{h.hexdigest()[:16]}"


def _get_indexed_hashes(collection: chromadb.Collection) -> dict[str, str]:
    """
    Returns {source_file: document_hash} for all indexed files.
    """
    result = collection.get(include=["metadatas"])
    hashes: dict[str, str] = {}
    if result["metadatas"]:
        for meta in result["metadatas"]:
            fname = meta.get("source_file", "")
            dhash = meta.get("document_hash", "")
            if fname and dhash:
                hashes[fname] = dhash
    return hashes


def _delete_file_chunks(collection: chromadb.Collection, source_file: str) -> None:
    """Delete all chunks of a file from collection."""
    collection.delete(where={"source_file": source_file})


async def index_all_documents() -> dict:
    """
    Main indexing function. Runs at startup with a lock to prevent race conditions.
    """
    async with _indexing_lock:
        # Ensure KB_DIR exists
        if not KB_DIR.exists():
            await asyncio.to_thread(KB_DIR.mkdir, parents=True, exist_ok=True)

        collection = await asyncio.to_thread(get_chroma_collection)
        indexed_hashes = await asyncio.to_thread(_get_indexed_hashes, collection)

        pdf_files = list(KB_DIR.glob("*.pdf"))
        if not pdf_files:
            log.warning(
                "rag.indexer",
                message="knowledge_base folder is empty, RAG context will be empty",
            )
            return {"indexed": 0, "skipped": 0, "errors": []}

        stats = {"indexed": 0, "skipped": 0, "errors": []}

        # Delete chunks of files that no longer exist
        existing_names = {f.name for f in pdf_files}
        for fname in list(indexed_hashes.keys()):
            if fname not in existing_names:
                await asyncio.to_thread(_delete_file_chunks, collection, fname)
                log.info("rag.indexer", action="deleted_stale", file=fname)

        for pdf_path in pdf_files:
            fname = pdf_path.name
            file_hash = await asyncio.to_thread(_file_hash, pdf_path)

            # Skip if hash hasn't changed
            if indexed_hashes.get(fname) == file_hash:
                log.info("rag.indexer", action="skipped_unchanged", file=fname)
                stats["skipped"] += 1
                continue

            # If file changed, delete old chunks first
            if fname in indexed_hashes:
                await asyncio.to_thread(_delete_file_chunks, collection, fname)

            try:
                chunk_count = await _index_single_pdf(collection, pdf_path, file_hash)
                log.info(
                    "rag.indexer", action="indexed", file=fname, chunks=chunk_count
                )
                stats["indexed"] += chunk_count
            except EmbeddingAPIError as e:
                log.error(
                    "rag.indexer", action="embedding_error", file=fname, error=str(e)
                )
                stats["errors"].append({"file": fname, "error": str(e)})
            except Exception as e:
                log.error("rag.indexer", action="parse_error", file=fname, error=str(e))
                stats["errors"].append({"file": fname, "error": str(e)})

        return stats


async def _index_single_pdf(
    collection: chromadb.Collection,
    pdf_path: Path,
    file_hash: str,
) -> int:
    """
    Parses PDF, chunks text, gets embeddings, and saves to ChromaDB.
    """

    def parse_pdf():
        chunks_out: list[TextChunk] = []
        doc = fitz.open(str(pdf_path))
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if not text:
                continue
            p_chunks = chunk_text(
                text=text,
                source_file=pdf_path.name,
                page=page_num,
                document_hash=file_hash,
                chunk_size=settings.RAG_CHUNK_SIZE,
                overlap=settings.RAG_CHUNK_OVERLAP,
            )
            chunks_out.extend(p_chunks)
        doc.close()
        return chunks_out

    all_chunks = await asyncio.to_thread(parse_pdf)

    if not all_chunks:
        return 0

    # Batch get embeddings (this is already async)
    texts = [c.text for c in all_chunks]
    embeddings = await get_embeddings_batch(texts)

    # Upsert to ChromaDB (sync operation)
    def upsert_to_chroma():
        collection.upsert(
            ids=[c.chunk_id for c in all_chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {
                    "source_file": c.source_file,
                    "page": c.page,
                    "chunk_index": c.chunk_index,
                    "document_hash": c.document_hash,
                }
                for c in all_chunks
            ],
        )

    await asyncio.to_thread(upsert_to_chroma)

    return len(all_chunks)
