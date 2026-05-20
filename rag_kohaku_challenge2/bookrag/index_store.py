from __future__ import annotations

import argparse
import json
import pickle
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from .embeddings import Embedder, build_node_embeddings, load_embeddings, save_embeddings
from .preprocess import build_tree_from_file, build_tree_from_text, load_nodes, save_nodes
from .schema import Node
from .text_utils import bm25_tokenize


SEARCH_TYPES = {"sentence", "paragraph"}


class BookIndex:
    def __init__(
        self,
        nodes: dict[str, Node],
        searchable_ids: list[str],
        embed_model_name: str,
        faiss_index: faiss.Index,
        bm25: BM25Okapi,
        bm25_tokens: list[list[str]],
    ) -> None:
        self.nodes = nodes
        self.searchable_ids = searchable_ids
        self.embed_model_name = embed_model_name
        self.faiss_index = faiss_index
        self.bm25 = bm25
        self.bm25_tokens = bm25_tokens


def build_index(
    book_path: str | Path,
    index_dir: str | Path,
    embed_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
) -> None:
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)

    nodes = build_tree_from_file(book_path)
    embedder = Embedder(embed_model_name)
    embeddings = build_node_embeddings(nodes, embedder)

    searchable_ids = [nid for nid, n in nodes.items() if n.type in SEARCH_TYPES and nid in embeddings]
    vectors = np.vstack([embeddings[nid] for nid in searchable_ids]).astype("float32")

    faiss_index = faiss.IndexFlatIP(vectors.shape[1])
    faiss_index.add(vectors)

    bm25_tokens = [bm25_tokenize(nodes[nid].text) for nid in searchable_ids]

    save_nodes(nodes, index_dir / "nodes.json")
    save_embeddings({nid: embeddings[nid] for nid in searchable_ids}, index_dir / "search_embeddings.npz")
    faiss.write_index(faiss_index, str(index_dir / "vectors.faiss"))

    meta = {
        "embed_model_name": embed_model_name,
        "searchable_ids": searchable_ids,
        "bm25_tokens": bm25_tokens,
        "search_types": sorted(SEARCH_TYPES),
    }
    (index_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    stats: dict[str, int] = {}
    for n in nodes.values():
        stats[n.type] = stats.get(n.type, 0) + 1
    print("Index saved:", index_dir)
    print("Node stats:", stats)
    print("Searchable:", len(searchable_ids))


def load_index(index_dir: str | Path) -> BookIndex:
    index_dir = Path(index_dir)
    nodes = load_nodes(index_dir / "nodes.json")
    meta = json.loads((index_dir / "meta.json").read_text(encoding="utf-8"))
    faiss_index = faiss.read_index(str(index_dir / "vectors.faiss"))
    bm25_tokens = meta["bm25_tokens"]
    return BookIndex(
        nodes=nodes,
        searchable_ids=meta["searchable_ids"],
        embed_model_name=meta["embed_model_name"],
        faiss_index=faiss_index,
        bm25=BM25Okapi(bm25_tokens),
        bm25_tokens=bm25_tokens,
    )


def main() -> None:
    parser = argparse.ArgumentParser("Build/load book RAG index")
    parser.add_argument("--book", type=str, default="book.txt")
    parser.add_argument("--index-dir", type=str, default="data/book_index")
    parser.add_argument("--model", type=str, default="paraphrase-multilingual-MiniLM-L12-v2")
    args = parser.parse_args()

    book_path = Path(args.book)
    if not book_path.exists():
        print(f"{book_path} not found, creating demo book.")
        book_path.parent.mkdir(parents=True, exist_ok=True) if book_path.parent != Path('.') else None
        book_path.write_text("""
# 第一章 RAG
RAG 包含索引、检索、重排和生成。向量检索适合语义相似，BM25 适合关键词。
Parent retrieval 先检索小块，再扩展到父段落。

# 第二章 GraphRAG
GraphRAG 从文本抽取实体和关系，构建社区摘要，适合全局问题。
""", encoding="utf-8")

    build_index(book_path, args.index_dir, args.model)
    loaded = load_index(args.index_dir)
    print("Loaded index:", len(loaded.searchable_ids), "searchable nodes")


if __name__ == "__main__":
    main()
