from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """Kohaku-style hierarchical node.

    type: document / section / paragraph / sentence / summary / entity
    """

    id: str
    type: str
    text: str
    parent_id: str | None = None
    child_ids: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hit:
    node_id: str
    score: float
    source: str
    rank: int = 0
    debug: dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    ref_id: str
    text: str
    title: str = ""
    source_node_ids: list[str] = field(default_factory=list)
    score: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


if __name__ == "__main__":
    # Minimal self-test
    doc = Node(id="doc:0", type="document", text="book.txt")
    sec = Node(id="sec:0", type="section", text="第一章", parent_id=doc.id)
    doc.child_ids.append(sec.id)
    hit = Hit(node_id=sec.id, score=0.9, source="dense", rank=1)
    print(doc)
    print(sec)
    print(hit)
