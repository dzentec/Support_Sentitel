from app.rag.chunker import chunk_text


def test_chunker():
    text = (
        "This is a test paragraph.\n\nThis is another paragraph that is hopefully long enough to be chunked if we set the size small. "
        * 10
    )
    chunks = chunk_text(text, "test.pdf", 1, "hash123", chunk_size=20, overlap=5)
    print(f"Total chunks: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"Chunk {i}: {c.text[:50]}...")


if __name__ == "__main__":
    test_chunker()
