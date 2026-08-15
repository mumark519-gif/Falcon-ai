from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math
import re

from app.documents.text_splitter import split_text
from app.services.reranker import rerank_results
from app.services.embedding_provider import EmbeddingProvider

_embedding_provider = EmbeddingProvider()

class SearchResults(list):
    """List-compatible search result with convenient text semantics."""
    def text(self) -> str:
        return "\n\n".join(
            str(item.get("text", "")) if isinstance(item, dict) else str(item)
            for item in self
        )
    def lower(self) -> str:
        return self.text().lower()
    def __contains__(self, item) -> bool:
        if isinstance(item, str):
            return item in self.text()
        return super().__contains__(item)

class _FallbackCollection:
    def __init__(self):
        self.rows: list[dict[str, Any]] = []
    def count(self):
        return len(self.rows)
    def add(self, *, ids, embeddings, documents, metadatas):
        for i, doc, meta, emb in zip(ids, documents, metadatas, embeddings):
            self.rows = [r for r in self.rows if r["id"] != i]
            self.rows.append({"id": i, "document": doc, "metadata": meta, "embedding": emb})
    def get(self, where=None):
        rows = self.rows
        if where:
            rows = [r for r in rows if all(r["metadata"].get(k) == v for k, v in where.items())]
        return {
            "documents": [r["document"] for r in rows],
            "metadatas": [r["metadata"] for r in rows],
        }
    def query(self, *, query_embeddings, n_results=8, where=None):
        rows = self.rows
        if where:
            rows = [r for r in rows if all(r["metadata"].get(k) == v for k, v in where.items())]
        q = query_embeddings[0] if query_embeddings else []
        def cosine(a,b):
            if not a or not b: return 0.0
            n=min(len(a),len(b))
            dot=sum(a[i]*b[i] for i in range(n))
            na=math.sqrt(sum(x*x for x in a[:n])); nb=math.sqrt(sum(x*x for x in b[:n]))
            return dot/(na*nb) if na and nb else 0.0
        ranked=sorted(rows,key=lambda r:cosine(q,r["embedding"]),reverse=True)[:n_results]
        return {
            "documents":[[r["document"] for r in ranked]],
            "metadatas":[[r["metadata"] for r in ranked]],
            "distances":[[1-cosine(q,r["embedding"]) for r in ranked]],
        }

try:
    import chromadb
    _client = chromadb.PersistentClient(path="data/chroma")
    collection = _client.get_or_create_collection(name="falcon_documents")
except Exception:
    _client = None
    collection = _FallbackCollection()

def _normalize_document(document: Any) -> dict:
    if isinstance(document, str):
        return {"type": "text", "content": document, "metadata": {}}
    if not isinstance(document, dict):
        raise TypeError("Document must be a string or dictionary.")
    document_type = str(document.get("type", "text") or "text").lower()
    metadata = document.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    if document_type == "pdf":
        text = "\n\n".join(
            page.get("text", "") for page in document.get("pages", [])
            if isinstance(page, dict)
        )
    elif document_type == "docx":
        text = "\n\n".join(
            p.get("text", "") for p in document.get("paragraphs", [])
            if isinstance(p, dict)
        )
    else:
        text = document.get("content", "")
    return {"type": document_type, "content": text or "", "metadata": metadata}

def add_document(username: str, document_id: str, document: Any):
    normalized = _normalize_document(document)
    text = normalized["content"]
    if not text.strip():
        return {"success": False, "document_id": document_id, "chunks": 0, "error": "Document contains no text."}
    chunks = split_text(text)
    if not chunks:
        return {"success": False, "document_id": document_id, "chunks": 0, "error": "Document produced no chunks."}
    metadata = normalized["metadata"]
    title = metadata.get("title") or document_id
    added = 0
    for index, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        embedding = _embedding_provider.embed(chunk)
        collection.add(
            ids=[f"{username}_{document_id}_{index}"],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{
                "username": username,
                "document": document_id,
                "chunk": index,
                "title": title,
                "type": normalized["type"],
                "source": "upload",
                "page": metadata.get("page", 0),
                "section": metadata.get("section", ""),
            }],
        )
        added += 1
    return {"success": True, "document_id": document_id, "chunks": added}

def search_documents(username: str, query: str, n_results: int = 8) -> SearchResults:
    if not str(query or "").strip():
        return SearchResults()
    embedding = _embedding_provider.embed(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where={"username": username},
    )
    docs = (results.get("documents") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    output = SearchResults()
    for doc, distance, metadata in zip(docs, distances, metas):
        score = max(0.0, round((1 - float(distance) / 2) * 100, 2))
        output.append({
            "text": doc,
            "metadata": metadata or {},
            "distance": float(distance),
            "score": score,
        })
    return output

def keyword_search(username: str, query: str):
    query = str(query or "").strip().lower()
    if not query:
        return []
    results = collection.get(where={"username": username})
    docs = results.get("documents", [])
    metas = results.get("metadatas", [])
    words = [w for w in re.split(r"\W+", query) if w]
    matches=[]
    for doc, meta in zip(docs, metas):
        text=doc.lower()
        score=sum(1 for w in words if w in text)
        if score:
            matches.append({"text":doc,"metadata":meta or {},"keyword_score":score})
    return sorted(matches,key=lambda x:x["keyword_score"],reverse=True)[:8]

def hybrid_search(username: str, query: str):
    if not str(query or "").strip():
        return []
    vector_results=search_documents(username,query)
    keyword_results=keyword_search(username,query)
    merged={}
    for result in vector_results:
        merged[result["text"]]={**result,"final_score":result.get("score",0)*0.7}
    for result in keyword_results:
        text=result["text"]; bonus=result.get("keyword_score",0)*3
        if text in merged: merged[text]["final_score"]+=bonus
        else: merged[text]={**result,"final_score":bonus}
    return rerank_results(query,sorted(merged.values(),key=lambda x:x.get("final_score",0),reverse=True))
