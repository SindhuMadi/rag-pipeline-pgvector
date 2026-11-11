def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Invalid size or Overlap. ")

    step = size - overlap
    chunks = []
    
    start = 0
    while start < len(text):
        piece = text[start:start+size]
        if piece.strip():
            chunks.append(piece)
        if start+size >= len(text):
            break
        start = start+step       

    return chunks