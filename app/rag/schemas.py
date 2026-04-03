from dataclasses import dataclass
from typing import List


@dataclass
class TextChunk:
    """A single chunk of text from a PDF."""

    chunk_id: str  # "filename::page::chunk_index"
    text: str
    source_file: str
    page: int
    chunk_index: int
    document_hash: str


@dataclass
class RetrievedChunk:
    """A chunk returned by the Retriever."""

    text: str
    source_file: str
    page: int
    score: float  # cosine similarity (0.0 – 1.0)


@dataclass
class KBContext:
    """Final context for the Gemini prompt."""

    chunks: List[RetrievedChunk]
    is_empty: bool  # True if no chunks found / all below threshold

    def to_prompt_block(self) -> str:
        """Formats context into an XML block for the prompt."""
        if self.is_empty:
            return ""
        parts = []
        for chunk in self.chunks:
            parts.append(
                f"[Source: {chunk.source_file}, page {chunk.page}]\n{chunk.text}"
            )
        body = "\n\n".join(parts)
        return f"<knowledge_base>\n{body}\n</knowledge_base>"
