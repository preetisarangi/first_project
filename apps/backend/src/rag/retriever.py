"""Knowledge Base Retriever Module.

Embeds user requirements/specs with FastEmbed (BAAI/bge-small-en-v1.5)
and retrieves top relevant Playwright code snippets from Supabase pgvector.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from fastembed import TextEmbedding
except ImportError:
    TextEmbedding = None  # type: ignore

from src.db.supabase_client import get_supabase_client

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"


@dataclass
class RetrievedSnippet:
    id: Optional[int]
    file_path: str
    chunk_type: str
    content: str
    metadata: Dict[str, Any]
    similarity: float


class KnowledgeRetriever:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._embedder: Optional[Any] = None

    @property
    def embedder(self) -> Any:
        if self._embedder is None:
            if TextEmbedding is None:
                raise RuntimeError(
                    "The 'fastembed' library is not installed. "
                    "Please install it using 'pip install fastembed'."
                )
            self._embedder = TextEmbedding(model_name=self.model_name)
        return self._embedder

    def embed_query(self, query: str) -> List[float]:
        """Generate a 384-dimensional dense embedding for the search query."""
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        # FastEmbed expects an iterable of strings
        embeddings = list(self.embedder.embed([query.strip()]))
        raw_emb = embeddings[0]
        return raw_emb.tolist() if hasattr(raw_emb, "tolist") else list(raw_emb)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        match_threshold: float = 0.2,
        chunk_type: Optional[str] = None,
    ) -> List[RetrievedSnippet]:
        """Query Supabase pgvector via RPC match_test_chunks.

        Args:
            query: The user story, specification, or search phrase.
            top_k: Maximum number of snippets to return (default: 3).
            match_threshold: Cosine similarity floor (0.0 to 1.0).
            chunk_type: Optional filter ('page_object', 'utility', 'spec_pattern').

        Returns:
            List of RetrievedSnippet sorted by descending similarity.
        """
        # 1. Embed query
        query_vector = self.embed_query(query)

        # 2. Acquire Supabase client
        supabase = get_supabase_client()

        # 3. Call Supabase RPC function match_test_chunks
        try:
            params = {
                "query_embedding": query_vector,
                "match_threshold": match_threshold,
                "match_count": top_k,
                "filter_chunk_type": chunk_type,
            }
            response = supabase.rpc("match_test_chunks", params).execute()
            data = response.data or []

            results: List[RetrievedSnippet] = []
            for item in data:
                results.append(
                    RetrievedSnippet(
                        id=item.get("id"),
                        file_path=item.get("file_path", "unknown"),
                        chunk_type=item.get("chunk_type", "unknown"),
                        content=item.get("content", ""),
                        metadata=item.get("metadata", {}),
                        similarity=float(item.get("similarity", 0.0)),
                    )
                )
            return results
        except Exception as exc:
            # Provide actionable debugging message
            raise RuntimeError(
                f"Failed to query Supabase vector RPC 'match_test_chunks': {exc}. "
                "Ensure you have executed apps/backend/src/rag/schema.sql in Supabase SQL editor."
            ) from exc


# Convenient function export for LangGraph nodes
def retrieve_relevant_context(
    query: str,
    top_k: int = 3,
    chunk_type: Optional[str] = None,
) -> List[str]:
    """Retrieve top_k code snippets as a formatted list of string blocks."""
    retriever = KnowledgeRetriever()
    snippets = retriever.retrieve(query=query, top_k=top_k, chunk_type=chunk_type)
    return [
        f"// [{s.chunk_type.upper()}] from {s.file_path} (similarity: {s.similarity:.2f})\n{s.content}"
        for s in snippets
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Search Playwright patterns from Supabase pgvector."
    )
    parser.add_argument("query", help="Search query (e.g. 'login flow with auth token assertion')")
    parser.add_argument("--top-k", "-k", type=int, default=3, help="Number of results (default: 3)")
    args = parser.parse_args()

    retriever = KnowledgeRetriever()
    try:
        results = retriever.retrieve(args.query, top_k=args.top_k)
        print(f"\n[✓] Found {len(results)} relevant snippets for query: '{args.query}'\n")
        for idx, res in enumerate(results, 1):
            print(f"--- #{idx} [{res.chunk_type.upper()}] {res.file_path} (similarity: {res.similarity:.3f}) ---")
            print(res.content)
            print()
    except Exception as err:
        print(f"\n[ERROR] Retrieval failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
