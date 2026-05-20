from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np

from .embeddings import Embedder
from .index_store import load_index
from .query_planner import llm_query_plan, simple_query_plan
from .schema import Hit
from .text_utils import bm25_tokenize


def reciprocal_rank_fusion(rank_lists: list[list[Hit]], k: int = 60) -> list[Hit]:
    """RRF: stable fusion for dense/BM25/multi-query results."""
    scores: dict[str, float] = defaultdict(float)
    sources: dict[str, set[str]] = defaultdict(set)
    debug: dict[str, dict] = defaultdict(dict)

    for hits in rank_lists:
        for rank, hit in enumerate(hits, start=1):
            scores[hit.node_id] += 1.0 / (k + rank)
            sources[hit.node_id].add(hit.source)
            debug[hit.node_id].setdefault("raw", []).append({
                "source": hit.source,
                "rank": rank,
                "score": hit.score,
                **hit.debug,
            })

    fused = [
        Hit(node_id=nid, score=score, source="+".join(sorted(sources[nid])), debug=debug[nid])
        for nid, score in scores.items()
    ]
    fused.sort(key=lambda x: x.score, reverse=True)
    for i, h in enumerate(fused, start=1):
        h.rank = i
    return fused


class HybridRetriever:
    def __init__(self, index_dir: str | Path) -> None:
        self.book_index = load_index(index_dir)
        self.embedder = Embedder(self.book_index.embed_model_name)

    def dense_search(self, query: str, top_k: int = 10) -> list[Hit]:
        qv = self.embedder.encode([query])
        scores, idxs = self.book_index.faiss_index.search(qv, top_k)
        hits: list[Hit] = []
        for rank, (score, idx) in enumerate(zip(scores[0], idxs[0]), start=1):
            if idx < 0:
                continue
            nid = self.book_index.searchable_ids[int(idx)]
            hits.append(Hit(node_id=nid, score=float(score), source="dense", rank=rank, debug={"query": query}))
        return hits

    def bm25_search(self, query: str, top_k: int = 10) -> list[Hit]:
        scores = self.book_index.bm25.get_scores(bm25_tokenize(query))
        order = np.argsort(scores)[::-1][:top_k]
        hits: list[Hit] = []
        for rank, idx in enumerate(order, start=1):
            score = float(scores[int(idx)])
            if score <= 0:
                continue
            nid = self.book_index.searchable_ids[int(idx)]
            hits.append(Hit(node_id=nid, score=score, source="bm25", rank=rank, debug={"query": query}))
        return hits

    def retrieve(
        self,
        question: str,
        top_k_per_query: int = 10,
        final_k: int = 20,
        max_queries: int = 4,
        use_llm_planner: bool = False,
    ) -> list[Hit]:
        queries = llm_query_plan(question, max_queries=max_queries) if use_llm_planner else simple_query_plan(question, max_queries=max_queries)
        rank_lists: list[list[Hit]] = []
        for q in queries:
            rank_lists.append(self.dense_search(q, top_k=top_k_per_query))
            rank_lists.append(self.bm25_search(q, top_k=top_k_per_query))
        fused = reciprocal_rank_fusion(rank_lists)
        return fused[:final_k]


def main() -> None:
    parser = argparse.ArgumentParser("Test hybrid retrieval")
    parser.add_argument("--index-dir", default="data/book_index")
    parser.add_argument("--question", default="GraphRAG 和向量检索有什么区别？")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--llm-planner", action="store_true")
    args = parser.parse_args()

    retriever = HybridRetriever(args.index_dir)
    hits = retriever.retrieve(args.question, final_k=args.top_k, use_llm_planner=args.llm_planner)
    for h in hits:
        n = retriever.book_index.nodes[h.node_id]
        print(f"#{h.rank} {h.score:.4f} {h.node_id} {n.type} {h.source}")
        print(n.text[:160].replace("\n", " "))
        print()


if __name__ == "__main__":
    main()
