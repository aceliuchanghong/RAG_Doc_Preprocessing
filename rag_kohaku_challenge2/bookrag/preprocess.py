from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .schema import Node
from .text_utils import normalize_text, split_paragraphs, split_sections, split_sentence_spans


def build_tree_from_text(text: str, source: str = "book.txt") -> dict[str, Node]:
    text = normalize_text(text)
    nodes: dict[str, Node] = {}

    doc_id = "doc:0"
    nodes[doc_id] = Node(
        id=doc_id,
        type="document",
        text=source,
        meta={"source": source},
    )

    sections = split_sections(text)
    for si, (title, section_text) in enumerate(sections):
        sec_id = f"sec:{si}"
        nodes[sec_id] = Node(
            id=sec_id,
            type="section",
            text=title,
            parent_id=doc_id,
            meta={"section_index": si, "title": title, "source": source},
        )
        nodes[doc_id].child_ids.append(sec_id)

        paragraphs = split_paragraphs(section_text)
        for pi, para in enumerate(paragraphs):
            pid = f"sec:{si}:p:{pi}"
            nodes[pid] = Node(
                id=pid,
                type="paragraph",
                text=para,
                parent_id=sec_id,
                meta={
                    "source": source,
                    "section_index": si,
                    "section_title": title,
                    "paragraph_index": pi,
                },
            )
            nodes[sec_id].child_ids.append(pid)

            spans = split_sentence_spans(para)
            for ti, span in enumerate(spans):
                sid = f"sec:{si}:p:{pi}:s:{ti}"
                nodes[sid] = Node(
                    id=sid,
                    type="sentence",
                    text=span,
                    parent_id=pid,
                    meta={
                        "source": source,
                        "section_index": si,
                        "section_title": title,
                        "paragraph_index": pi,
                        "sentence_index": ti,
                    },
                )
                nodes[pid].child_ids.append(sid)
    return nodes


def build_tree_from_file(book_path: str | Path) -> dict[str, Node]:
    path = Path(book_path)
    return build_tree_from_text(path.read_text(encoding="utf-8"), source=str(path))


def save_nodes(nodes: dict[str, Node], out_path: str | Path) -> None:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = {node_id: asdict(node) for node_id, node in nodes.items()}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_nodes(path: str | Path) -> dict[str, Node]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {node_id: Node(**item) for node_id, item in data.items()}


def main() -> None:
    parser = argparse.ArgumentParser("Preprocess book.txt into Kohaku-style tree")
    parser.add_argument("--book", type=str, default="book.txt")
    parser.add_argument("--out", type=str, default="data/nodes.json")
    args = parser.parse_args()

    if Path(args.book).exists():
        nodes = build_tree_from_file(args.book)
    else:
        print(f"{args.book} not found, using built-in demo text.")
        demo = """
# 第一章 RAG
RAG 通常包含索引、检索、重排和生成。向量检索适合语义相似，BM25 适合关键词和专有名词。

Parent retrieval 会先检索小块，再扩展到父段落，避免上下文缺失。

# 第二章 GraphRAG
GraphRAG 会从文本中抽取实体和关系，并使用社区摘要回答全局问题。
"""
        nodes = build_tree_from_text(demo, source="demo")

    save_nodes(nodes, args.out)
    stats: dict[str, int] = {}
    for n in nodes.values():
        stats[n.type] = stats.get(n.type, 0) + 1
    print("Saved:", args.out)
    print("Stats:", stats)
    for k, v in list(nodes.items())[:5]:
        print(k, v.type, v.text[:80].replace("\n", " "))


if __name__ == "__main__":
    main()
