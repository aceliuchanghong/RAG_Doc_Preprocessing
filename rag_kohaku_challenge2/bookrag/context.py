from __future__ import annotations

import argparse
from pathlib import Path

from .index_store import load_index
from .retrieval import HybridRetriever
from .schema import Evidence, Hit, Node


def _section_title(nodes: dict[str, Node], node: Node) -> str:
    cur = node
    while cur.parent_id:
        parent = nodes[cur.parent_id]
        if parent.type == "section":
            return parent.meta.get("title", parent.text)
        cur = parent
    return node.meta.get("section_title", "")


def expand_hit_to_parent(nodes: dict[str, Node], hit: Hit) -> Evidence:
    """RAG-Challenge-2 style parent retrieval.

    Search small child nodes, but answer with parent paragraph/section context.
    """
    node = nodes[hit.node_id]
    if node.type == "sentence" and node.parent_id:
        parent = nodes[node.parent_id]
        return Evidence(
            ref_id=parent.id,
            text=parent.text,
            title=_section_title(nodes, parent),
            source_node_ids=[hit.node_id],
            score=hit.score,
            meta={"expanded_from": node.type},
        )
    return Evidence(
        ref_id=node.id,
        text=node.text,
        title=_section_title(nodes, node),
        source_node_ids=[hit.node_id],
        score=hit.score,
        meta={"expanded_from": node.type},
    )


def expand_hit_to_sentence_window(nodes: dict[str, Node], hit: Hit, window: int = 1) -> Evidence:
    """LlamaIndex Sentence Window-like expansion.

    If a sentence/span is retrieved, include neighboring spans in the same paragraph.
    """
    node = nodes[hit.node_id]
    if node.type != "sentence" or not node.parent_id:
        return expand_hit_to_parent(nodes, hit)

    parent = nodes[node.parent_id]
    child_ids = parent.child_ids
    try:
        pos = child_ids.index(node.id)
    except ValueError:
        return expand_hit_to_parent(nodes, hit)

    selected = child_ids[max(0, pos - window): min(len(child_ids), pos + window + 1)]
    text = "".join(nodes[cid].text for cid in selected)
    return Evidence(
        ref_id=f"{parent.id}:window:{pos}",
        text=text,
        title=_section_title(nodes, parent),
        source_node_ids=selected,
        score=hit.score,
        meta={"expanded_from": "sentence_window", "window": window, "parent_id": parent.id},
    )


def dedupe_evidence(evidence: list[Evidence]) -> list[Evidence]:
    best: dict[str, Evidence] = {}
    for ev in evidence:
        key = ev.ref_id
        if key not in best or ev.score > best[key].score:
            best[key] = ev
    out = list(best.values())
    out.sort(key=lambda x: x.score, reverse=True)
    return out


def build_context_block(evidence: list[Evidence], max_chars: int = 8000) -> str:
    parts = []
    used = 0
    for i, ev in enumerate(evidence, start=1):
        block = f"[E{i}; ref_id={ev.ref_id}; section={ev.title}; score={ev.score:.4f}]\n{ev.text}"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n---\n\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser("Test context expansion")
    parser.add_argument("--index-dir", default="data/book_index")
    parser.add_argument("--question", default="parent retrieval 是什么？")
    parser.add_argument("--mode", choices=["parent", "window"], default="parent")
    args = parser.parse_args()

    retriever = HybridRetriever(args.index_dir)
    hits = retriever.retrieve(args.question, final_k=5)
    nodes = retriever.book_index.nodes
    if args.mode == "parent":
        evs = [expand_hit_to_parent(nodes, h) for h in hits]
    else:
        evs = [expand_hit_to_sentence_window(nodes, h, window=1) for h in hits]
    evs = dedupe_evidence(evs)
    print(build_context_block(evs))


if __name__ == "__main__":
    main()
