import re
from typing import List
from app.rag.schemas import TextChunk


def chunk_text(
    text: str,
    source_file: str,
    page: int,
    document_hash: str,
    chunk_size: int = 500,  # in tokens (approx, 1 token ≈ 4 chars)
    overlap: int = 50,
) -> List[TextChunk]:
    """
    Splits page text into overlapping chunks.
    Ensures overlap doesn't break words by snapping to nearest space.
    """
    char_size = chunk_size * 4  # rough conversion tokens → chars
    char_overlap = overlap * 4

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    sentences = []
    for para in paragraphs:
        # Split paragraph into sentences
        parts = re.split(r"(?<=[.!?])\s+", para)
        sentences.extend(parts)

    chunks: List[TextChunk] = []
    current = ""
    chunk_idx = 0

    for sentence in sentences:
        if len(current) + len(sentence) <= char_size:
            current += (" " if current else "") + sentence
        else:
            if len(current) >= 50:
                chunks.append(
                    TextChunk(
                        chunk_id=f"{source_file}::{page}::{chunk_idx}",
                        text=current.strip(),
                        source_file=source_file,
                        page=page,
                        chunk_index=chunk_idx,
                        document_hash=document_hash,
                    )
                )
                chunk_idx += 1

            # Smart Overlap: find a space boundary to avoid breaking words
            if len(current) > char_overlap:
                overlap_start = len(current) - char_overlap
                # Find the first space after our target start point to snap to word boundary
                space_idx = current.find(" ", overlap_start)
                if space_idx != -1 and space_idx < len(current) - 10:
                    overlap_text = current[space_idx:].strip()
                else:
                    overlap_text = current[-char_overlap:]
            else:
                overlap_text = current

            current = overlap_text + " " + sentence

    # Last chunk
    if len(current) >= 50:
        chunks.append(
            TextChunk(
                chunk_id=f"{source_file}::{page}::{chunk_idx}",
                text=current.strip(),
                source_file=source_file,
                page=page,
                chunk_index=chunk_idx,
                document_hash=document_hash,
            )
        )

    return chunks
