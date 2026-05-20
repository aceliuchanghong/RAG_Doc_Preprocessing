from __future__ import annotations

import argparse
import json

from bookrag.answer import answer_question
from bookrag.router import route_question


def main() -> None:
    parser = argparse.ArgumentParser("Ask book RAG")
    parser.add_argument("--index-dir", default="data/book_index")
    parser.add_argument("--question", required=True)
    parser.add_argument("--auto-route", action="store_true")
    parser.add_argument("--rerank", choices=["none", "cross", "llm"], default="none")
    parser.add_argument("--n-votes", type=int, default=1)
    args = parser.parse_args()

    rerank = args.rerank
    retrieval_k = 20
    context_k = 8
    if args.auto_route:
        cfg = route_question(args.question)
        rerank = cfg["rerank_method"]
        retrieval_k = cfg["retrieval_k"]
        context_k = cfg["context_k"]
        print("Route config:", json.dumps(cfg, ensure_ascii=False))

    result = answer_question(
        index_dir=args.index_dir,
        question=args.question,
        retrieval_k=retrieval_k,
        context_k=context_k,
        rerank_method=rerank,
        n_votes=args.n_votes,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
