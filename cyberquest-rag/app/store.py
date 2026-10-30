"""Knowledge base: extract -> chunk -> embed -> store (Chroma) -> search."""
import io
import re
import uuid

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

from .config import DATA_DIR, EMBED_MODEL, MIN_SCORE

_client = chromadb.PersistentClient(path=str(DATA_DIR / "chroma"))
_embed = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
_col = _client.get_or_create_collection(
    "cyberquest_kb", embedding_function=_embed, metadata={"hnsw:space": "cosine"}
)


def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    if name.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="ignore")
    raise ValueError("Only .pdf, .txt and .md files are supported")


def chunk_text(text: str, size: int = 800, overlap: int = 120) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) + 1 <= size:
            buf = f"{buf}\n{p}" if buf else p
            continue
        if buf:
            chunks.append(buf)
        while len(p) > size:  # very long paragraph: hard-split with overlap
            chunks.append(p[:size])
            p = p[size - overlap:]
        buf = p
    if buf:
        chunks.append(buf)
    return chunks


def add_document(title: str, text: str, tags: str = "") -> tuple[str, int]:
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No readable text found in the document")
    doc_id = uuid.uuid4().hex[:12]
    _col.add(
        ids=[f"{doc_id}-{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[
            {"doc_id": doc_id, "title": title, "tags": tags, "chunk": i}
            for i in range(len(chunks))
        ],
    )
    return doc_id, len(chunks)


def list_documents() -> list[dict]:
    metas = _col.get(include=["metadatas"])["metadatas"] or []
    docs: dict[str, dict] = {}
    for m in metas:
        d = docs.setdefault(
            m["doc_id"], {"doc_id": m["doc_id"], "title": m["title"], "tags": m["tags"], "chunks": 0}
        )
        d["chunks"] += 1
    return sorted(docs.values(), key=lambda d: d["title"])


def delete_document(doc_id: str) -> None:
    _col.delete(where={"doc_id": doc_id})


def search(query: str, k: int = 5) -> list[dict]:
    if _col.count() == 0:
        return []
    res = _col.query(query_texts=[query], n_results=min(k, _col.count()))
    hits = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        score = round(1 - dist, 3)
        if score >= MIN_SCORE:
            hits.append({"text": text, "title": meta["title"], "doc_id": meta["doc_id"], "score": score})
    return hits
