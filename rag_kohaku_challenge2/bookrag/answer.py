from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter

from .context import build_context_block, dedupe_evidence, expand_hit_to_parent
from .rerank import llm_rerank, local_cross_encoder_rerank
from .retrieval import HybridRetriever
from .schema import Evidence


def answer_once(question: str, context_block: str, model: str = "gpt-4o-mini", temperature: float = 0.1) -> dict:
    if not os.getenv("OPENAI_API_KEY"):
        return {
            "answer": "未设置 OPENAI_API_KEY，所以这里只返回证据，不调用 LLM 生成答案。",
            "citations": [],
            "is_blank": True,
        }
    from openai import OpenAI

    client = OpenAI()
    prompt = f"""
你只能根据 Context 回答问题。证据不足时不要编造。

Context:
{context_block}

Question:
{question}

输出 JSON：
{{
  "answer": "中文答案",
  "citations": ["ref_id1", "ref_id2"],
  "is_blank": false
}}
要求：citations 必须来自 Context 的 ref_id。
"""
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def abstention_aware_vote(results: list[dict]) -> dict:
    """Kohaku-like ensemble: if there are non-blank answers, ignore blank ones."""
    candidates = [r for r in results if not r.get("is_blank")]
    pool = candidates or results
    if not pool:
        return {"answer": "", "citations": [], "is_blank": True}
    keys = [re.sub(r"\s+", " ", r.get("answer", "")).strip().lower() for r in pool]
    winner, _ = Counter(keys).most_common(1)[0]
    for r, key in zip(pool, keys):
        if key == winner:
            return r
    return pool[0]


def answer_question(
    index_dir: str,
    question: str,
    retrieval_k: int = 20,
    context_k: int = 8,
    rerank_method: str = "none",
    n_votes: int = 1,
    answer_model: str = "gpt-4o-mini",
) -> dict:
    retriever = HybridRetriever(index_dir)
    hits = retriever.retrieve(question, final_k=retrieval_k)
    evs = dedupe_evidence([expand_hit_to_parent(retriever.book_index.nodes, h) for h in hits])

    if rerank_method == "cross":
        evs = local_cross_encoder_rerank(question, evs)
    elif rerank_method == "llm":
        evs = llm_rerank(question, evs)

    evs = evs[:context_k]
    context = build_context_block(evs)
    results = [answer_once(question, context, model=answer_model) for _ in range(max(1, n_votes))]
    final = abstention_aware_vote(results)
    final["evidence_preview"] = [
        {"ref_id": ev.ref_id, "section": ev.title, "score": ev.score, "text": ev.text[:200]} for ev in evs
    ]
    return final


def main() -> None:
    parser = argparse.ArgumentParser("Ask book RAG")
    parser.add_argument("--index-dir", default="data/book_index")
    parser.add_argument("--question", default="GraphRAG 和普通向量检索有什么区别？")
    parser.add_argument("--rerank", choices=["none", "cross", "llm"], default="none")
    parser.add_argument("--n-votes", type=int, default=1)
    parser.add_argument("--model", default="gpt-4o-mini")
    args = parser.parse_args()

    result = answer_question(
        args.index_dir,
        args.question,
        rerank_method=args.rerank,
        n_votes=args.n_votes,
        answer_model=args.model,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
