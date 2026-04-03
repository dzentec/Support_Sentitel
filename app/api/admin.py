from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from app.rag.indexer import index_all_documents, get_chroma_collection
from app.config import settings
import asyncio
import secrets

router = APIRouter(prefix="/admin/rag", tags=["admin"])
api_key_header = APIKeyHeader(name="X-Admin-Key")


async def verify_admin_key(key: str = Depends(api_key_header)):
    # CRITICAL: Prevent access if key is empty or whitespace
    if not settings.ADMIN_API_KEY or not settings.ADMIN_API_KEY.strip():
        raise HTTPException(
            status_code=403,
            detail="Admin API is disabled. Configure ADMIN_API_KEY in .env",
        )
    # Use compare_digest to prevent timing attacks
    if not secrets.compare_digest(key, settings.ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/reindex", dependencies=[Depends(verify_admin_key)])
async def reindex():
    """Reindex all documents without restarting."""
    stats = await index_all_documents()
    return {"status": "ok", "stats": stats}


@router.get("/stats", dependencies=[Depends(verify_admin_key)])
async def rag_stats():
    """Index statistics."""
    try:
        collection = await asyncio.to_thread(get_chroma_collection)
        count = await asyncio.to_thread(collection.count)

        # Retrieval of unique files
        result = await asyncio.to_thread(collection.get, include=["metadatas"])

        files = {}
        if result["metadatas"]:
            for meta in result["metadatas"]:
                fname = meta.get("source_file", "")
                if fname:
                    files[fname] = files.get(fname, 0) + 1

        return {
            "total_chunks": count,
            "documents": [{"file": k, "chunks": v} for k, v in files.items()],
            "warning": "Statistics based on full metadata scan."
            if count > 5000
            else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
