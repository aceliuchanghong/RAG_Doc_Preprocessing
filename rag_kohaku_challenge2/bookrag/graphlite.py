from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

from .preprocess import load_nodes
from .schema import Node
from .text_utils import bm25_tokenize


STOPWORDS = set("的 了 和 与 或 是 在 对 及 中 为 一个 一种 以及 通过 使用 进行 可以 这个 那个 如果 因此 because with from into the and of to in a an is are be on for".split())


def extract_terms(text: str, min_len: int = 2, top_n: int = 12) -> list[str]:
    """LLM-free pseudo entity extraction.

    Production upgrade: replace this with LLM/NER entity extraction.
    """
    # English long words / acronyms
    terms = re.findall(r"[A-Z][A-Za-z0-9\-]{2,}|[a-zA-Z][a-zA-Z0-9\-]{3,}", text)
    # Chinese 2-6 char terms using crude sliding windows over CJK runs.
    cjk_runs = re.findall(r"[\u4e00-\u9fff]{2,12}", text)
    for run in cjk_runs:
        for n in [2, 3, 4]:
            for i in range(0, max(0, len(run) - n + 1)):
                terms.append(run[i:i+n])
    terms = [t for t in terms if len(t) >= min_len and t.lower() not in STOPWORDS]
    freq = Counter(terms)
    return [t for t, _ in freq.most_common(top_n)]


def build_cooccurrence_graph(nodes: dict[str, Node], min_edge_weight: int = 2) -> nx.Graph:
    graph = nx.Graph()
    paragraph_nodes = [n for n in nodes.values() if n.type == "paragraph"]
    for node in paragraph_nodes:
        terms = list(dict.fromkeys(extract_terms(node.text, top_n=10)))
        for t in terms:
            graph.add_node(t, count=graph.nodes[t].get("count", 0) + 1 if t in graph else 1)
        for i, a in enumerate(terms):
            for b in terms[i + 1:]:
                if a == b:
                    continue
                if graph.has_edge(a, b):
                    graph[a][b]["weight"] += 1
                    graph[a][b]["paragraph_ids"].append(node.id)
                else:
                    graph.add_edge(a, b, weight=1, paragraph_ids=[node.id])
    remove_edges = [(a, b) for a, b, d in graph.edges(data=True) if d.get("weight", 0) < min_edge_weight]
    graph.remove_edges_from(remove_edges)
    return graph


def graph_expand_terms(graph: nx.Graph, query: str, max_terms: int = 8) -> list[str]:
    seeds = extract_terms(query, top_n=8)
    scored: Counter[str] = Counter()
    for seed in seeds:
        if seed not in graph:
            continue
        for nb in graph.neighbors(seed):
            scored[nb] += graph[seed][nb].get("weight", 1)
    return [t for t, _ in scored.most_common(max_terms)]


def save_graph(graph: nx.Graph, out_path: str | Path) -> None:
    data = nx.node_link_data(graph)
    Path(out_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_graph(path: str | Path) -> nx.Graph:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return nx.node_link_graph(data)


def main() -> None:
    parser = argparse.ArgumentParser("Build/test a tiny GraphRAG-like co-occurrence graph")
    parser.add_argument("--nodes", default="data/book_index/nodes.json")
    parser.add_argument("--out", default="data/book_graph.json")
    parser.add_argument("--query", default="GraphRAG 和向量检索的关系")
    args = parser.parse_args()

    nodes = load_nodes(args.nodes)
    graph = build_cooccurrence_graph(nodes)
    save_graph(graph, args.out)
    print("Saved graph:", args.out)
    print("Nodes:", graph.number_of_nodes(), "Edges:", graph.number_of_edges())
    print("Query expansion terms:", graph_expand_terms(graph, args.query))


if __name__ == "__main__":
    main()
