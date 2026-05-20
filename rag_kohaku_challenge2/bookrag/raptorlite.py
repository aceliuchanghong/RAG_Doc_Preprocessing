from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans

from .embeddings import Embedder
from .preprocess import load_nodes, save_nodes
from .schema import Node


def naive_summary(texts: list[str], max_chars: int = 700) -> str:
    """LLM-free summary: concatenate leading sentences.

    Production upgrade: replace with LLM abstractive summary.
    """
    joined = " ".join(t.strip().replace("\n", " ") for t in texts if t.strip())
    return joined[:max_chars]


def add_raptor_summaries(
    nodes: dict[str, Node],
    embed_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    n_clusters: int = 4,
    max_items: int = 120,
) -> dict[str, Node]:
    """RAPTOR-lite: cluster paragraphs and create summary nodes.

    True RAPTOR recursively embeds, clusters and summarizes; this teaching version
    adds one summary layer, enough to test the idea on book.txt.
    """
    paras = [n for n in nodes.values() if n.type == "paragraph"][:max_items]
    if len(paras) < 4:
        return nodes

    k = min(n_clusters, max(2, len(paras) // 3))
    embedder = Embedder(embed_model_name)
    vecs = embedder.encode([p.text for p in paras])
    labels = KMeans(n_clusters=k, n_init="auto", random_state=42).fit_predict(vecs)

    root_id = "raptor:root"
    nodes[root_id] = Node(
        id=root_id,
        type="summary_root",
        text="RAPTOR-lite summary root",
        parent_id="doc:0" if "doc:0" in nodes else None,
        meta={"method": "raptor_lite"},
    )
    if "doc:0" in nodes:
        nodes["doc:0"].child_ids.append(root_id)

    for cluster_id in range(k):
        members = [paras[i] for i, label in enumerate(labels) if int(label) == cluster_id]
        sid = f"raptor:summary:{cluster_id}"
        nodes[sid] = Node(
            id=sid,
            type="summary",
            text=naive_summary([m.text for m in members]),
            parent_id=root_id,
            child_ids=[m.id for m in members],
            meta={"method": "raptor_lite", "cluster_id": cluster_id, "member_count": len(members)},
        )
        nodes[root_id].child_ids.append(sid)
    return nodes


def main() -> None:
    parser = argparse.ArgumentParser("Add RAPTOR-lite summary nodes")
    parser.add_argument("--nodes", default="data/book_index/nodes.json")
    parser.add_argument("--out", default="data/nodes_with_raptor.json")
    parser.add_argument("--clusters", type=int, default=4)
    parser.add_argument("--model", default="paraphrase-multilingual-MiniLM-L12-v2")
    args = parser.parse_args()

    nodes = load_nodes(args.nodes)
    nodes = add_raptor_summaries(nodes, args.model, args.clusters)
    save_nodes(nodes, args.out)
    print("Saved:", args.out)
    for n in nodes.values():
        if n.type == "summary":
            print(n.id, n.meta, n.text[:160])


if __name__ == "__main__":
    main()
