from __future__ import annotations

import argparse
import json
from pathlib import Path

from .context import dedupe_evidence, expand_hit_to_parent
from .retrieval import HybridRetriever


def load_jsonl(path: str | Path) -> list[dict]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def evaluate_retrieval(index_dir: str, qa_path: str, k: int = 10) -> dict:
    """Evaluate recall@k / MRR with gold_refs.

    Expected qa.jsonl:
    {"question": "...", "gold_refs": ["sec:0:p:1"]}
    """
    retriever = HybridRetriever(index_dir)
    rows = load_jsonl(qa_path)
    recall_hits = 0
    mrr_total = 0.0
    details = []

    for row in rows:
        q = row["question"]
        gold = set(row.get("gold_refs", []))
        hits = retriever.retrieve(q, final_k=k)
        evs = dedupe_evidence([expand_hit_to_parent(retriever.book_index.nodes, h) for h in hits])[:k]
        refs = [ev.ref_id for ev in evs]
        found_rank = None
        for i, ref in enumerate(refs, start=1):
            if ref in gold:
                found_rank = i
                break
        if found_rank is not None:
            recall_hits += 1
            mrr_total += 1.0 / found_rank
        details.append({"question": q, "gold_refs": list(gold), "retrieved_refs": refs, "found_rank": found_rank})

    n = max(1, len(rows))
    return {"count": len(rows), f"recall@{k}": recall_hits / n, f"mrr@{k}": mrr_total / n, "details": details}


def main() -> None:
    parser = argparse.ArgumentParser("Evaluate retrieval")
    parser.add_argument("--index-dir", default="data/book_index")
    parser.add_argument("--qa", default="data/qa.jsonl")
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()

    qa_path = Path(args.qa)
    if not qa_path.exists():
        qa_path.parent.mkdir(parents=True, exist_ok=True)
        qa_path.write_text(
            '{"question":"parent retrieval 是什么？","gold_refs":["sec:0:p:0"]}\n',
            encoding="utf-8",
        )
        print("Demo qa.jsonl created:", qa_path)
    print(json.dumps(evaluate_retrieval(args.index_dir, args.qa, args.k), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
