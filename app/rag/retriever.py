import structlog
import chromadb
import asyncio

from app.rag.embeddings import get_embedding, EmbeddingAPIError
from app.rag.schemas import KBContext, RetrievedChunk
from app.rag.indexer import get_chroma_collection
from app.config import settings

log = structlog.get_logger()


async def retrieve(query_text: str) -> KBContext:
    """
    Find relevant chunks for the query text.
    """
    try:
        query_embedding = await get_embedding(query_text)
    except EmbeddingAPIError as e:
        log.warning(
            "rag.retriever",
            message="Embedding API unavailable, skipping RAG",
            error=str(e),
        )
        return KBContext(chunks=[], is_empty=True)

    try:
        collection = await asyncio.to_thread(get_chroma_collection)
        results = await asyncio.to_thread(
            collection.query,
            query_embeddings=[query_embedding],
            n_results=settings.RAG_TOP_K,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        log.error("rag.retriever", message="ChromaDB query error", error=str(e))
        return KBContext(chunks=[], is_empty=True)

    chunks: list[RetrievedChunk] = []
    if not results["documents"] or not results["documents"][0]:
        return KBContext(chunks=[], is_empty=True)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        # ChromaDB cosine distance is 1 - similarity.
        # dist = 0.0 (identical) -> score = 1.0
        # dist = 1.0 (orthogonal) -> score = 0.0
        # dist = 2.0 (opposite) -> score = -1.0
        score = 1.0 - dist

        if score < settings.RAG_MIN_SCORE:
            continue

        chunks.append(
            RetrievedChunk(
                text=doc,
                source_file=meta.get("source_file", "unknown"),
                page=meta.get("page", 0),
                score=round(score, 3),
            )
        )

    log.info(
        "rag.retriever",
        found=len(chunks),
        top_score=chunks[0].score if chunks else None,
    )
    return KBContext(chunks=chunks, is_empty=len(chunks) == 0)
