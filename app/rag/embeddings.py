import httpx
import asyncio
from app.config import settings
from app.utils.logging import logger

EMBEDDING_URL = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"


async def get_embedding(text: str, retries: int = 3) -> list[float]:
    """
    Get text embedding via Google Embedding API.
    Retries up to 3 times with exponential backoff for transient errors.
    """
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]},
    }
    headers = {"X-goog-api-key": settings.GEMINI_API_KEY}

    async with httpx.AsyncClient(timeout=15.0) as client:
        for attempt in range(retries):
            try:
                resp = await client.post(EMBEDDING_URL, json=payload, headers=headers)

                # If hit rate limit (429), wait longer
                if resp.status_code == 429:
                    wait = (2**attempt) + 1
                    logger.warning(
                        f"Embedding API rate limited (429). Retrying in {wait}s..."
                    )
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                return resp.json()["embedding"]["values"]

            except httpx.HTTPStatusError as e:
                # Don't retry on 4xx errors (except 429)
                if 400 <= e.response.status_code < 500:
                    logger.error(
                        f"Embedding API non-retryable error: {e.response.text}"
                    )
                    raise EmbeddingAPIError(f"API Error: {e.response.status_code}")
                raise
            except Exception as e:
                if attempt == retries - 1:
                    raise EmbeddingAPIError(
                        f"Embedding API unavailable after {retries} attempts: {e}"
                    )
                await asyncio.sleep(2**attempt)


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Fetch embeddings concurrently in small batches to respect rate limits
    while maximizing speed.
    """
    # Small chunks to avoid overwhelming the API
    chunk_size = 5
    all_embeddings = []

    for i in range(0, len(texts), chunk_size):
        batch = texts[i : i + chunk_size]
        tasks = [get_embedding(text) for text in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Failed to get embedding for chunk: {res}")
                # We can't easily skip because index order matters.
                # Re-raising for now as indexer handles stats.
                raise res
            all_embeddings.append(res)

        await asyncio.sleep(0.5)  # Throttle between small batches

    return all_embeddings


class EmbeddingAPIError(Exception):
    pass
