from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .preprocess import build_tree_from_text, load_nodes
from .schema import Node


def l2_normalize(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    return v if norm == 0 else v / norm


class Embedder:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        return self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 128,
        ).astype("float32")


def build_node_embeddings(
    nodes: dict[str, Node],
    embedder: Embedder,
    batch_size: int = 64,
) -> dict[str, np.ndarray]:
    """Sentence embeddings + bottom-up parent aggregation.

    Kohaku-like idea:
    1. leaf sentence/span nodes get direct embeddings;
    2. paragraph / section / document vectors are weighted averages of children.
    """
    embeddings: dict[str, np.ndarray] = {}

    leaf_ids = [nid for nid, n in nodes.items() if n.type == "sentence"]
    leaf_texts = [nodes[nid].text for nid in leaf_ids]
    vectors = embedder.encode(leaf_texts, batch_size=batch_size)
    for nid, vec in zip(leaf_ids, vectors):
        embeddings[nid] = vec

    for node_type in ["paragraph", "section", "document"]:
        for nid, node in nodes.items():
            if node.type != node_type:
                continue
            child_vecs = [embeddings[cid] for cid in node.child_ids if cid in embeddings]
            if not child_vecs:
                continue
            weights = np.array([max(1, len(nodes[cid].text)) for cid in node.child_ids if cid in embeddings], dtype="float32")
            mat = np.vstack(child_vecs)
            vec = np.average(mat, axis=0, weights=weights)
            embeddings[nid] = l2_normalize(vec).astype("float32")
    return embeddings


def save_embeddings(embeddings: dict[str, np.ndarray], out_path: str | Path) -> None:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, **embeddings)


def load_embeddings(path: str | Path) -> dict[str, np.ndarray]:
    data = np.load(path)
    return {k: data[k].astype("float32") for k in data.files}


def main() -> None:
    parser = argparse.ArgumentParser("Test embedding construction")
    parser.add_argument("--nodes", type=str, default="")
    parser.add_argument("--out", type=str, default="data/embeddings.npz")
    parser.add_argument("--model", type=str, default="paraphrase-multilingual-MiniLM-L12-v2")
    args = parser.parse_args()

    if args.nodes and Path(args.nodes).exists():
        nodes = load_nodes(args.nodes)
    else:
        nodes = build_tree_from_text("""
# 第一章
向量检索适合语义相似问题。BM25 适合关键词匹配。

Parent retrieval 先搜小块，再扩展父段落。
""", source="demo")

    emb = build_node_embeddings(nodes, Embedder(args.model))
    save_embeddings(emb, args.out)
    print("Saved:", args.out)
    print("Embedding count:", len(emb))
    first = next(iter(emb.items()))
    print("First:", first[0], first[1].shape, first[1][:5])


if __name__ == "__main__":
    main()
