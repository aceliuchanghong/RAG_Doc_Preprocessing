from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .context import build_context_block, dedupe_evidence, expand_hit_to_parent
from .retrieval import HybridRetriever
from .schema import Evidence, Hit


def local_cross_encoder_rerank(question: str, evidence: list[Evidence], model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> list[Evidence]:
    """Local rerank. Good default before using LLM rerank.

    First run may download the model.
    """
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(model_name)
        pairs = [(question, ev.text[:1800]) for ev in evidence]
        scores = model.predict(pairs)
        for ev, score in zip(evidence, scores):
            ev.score = float(score)
            ev.meta["rerank"] = "cross_encoder"
        evidence.sort(key=lambda x: x.score, reverse=True)
        return evidence
    except Exception as e:
        print("CrossEncoder rerank failed, keeping original order:", e)
        return evidence


def llm_rerank(question: str, evidence: list[Evidence], model: str = "gpt-4o-mini") -> list[Evidence]:
    if not os.getenv("OPENAI_API_KEY"):
        return evidence
    try:
        from openai import OpenAI
        client = OpenAI()
        items = []
        for i, ev in enumerate(evidence, start=1):
            items.append(f"{i}. ref_id={ev.ref_id}; section={ev.title}\n{ev.text[:1000]}")
        prompt = f"""
你是 RAG reranker。根据问题把证据按相关性重排。
问题：{question}
证据：
{chr(10).join(items)}
输出 JSON：{{"ranked_indices": [1, 3, 2]}}
"""
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        ranked = data.get("ranked_indices", [])
        new_order: list[Evidence] = []
        used = set()
        for idx in ranked:
            if isinstance(idx, int) and 1 <= idx <= len(evidence):
                i = idx - 1
                if i not in used:
                    used.add(i)
                    evidence[i].meta["rerank"] = "llm"
                    new_order.append(evidence[i])
        for i, ev in enumerate(evidence):
            if i not in used:
                new_order.append(ev)
        return new_order
    except Exception as e:
        print("LLM rerank failed, keeping original order:", e)
        return evidence


def main() -> None:
    parser = argparse.ArgumentParser("Test reranking")
    parser.add_argument("--index-dir", default="data/book_index")
    parser.add_argument("--question", default="GraphRAG 适合什么问题？")
    parser.add_argument("--method", choices=["none", "cross", "llm"], default="none")
    args = parser.parse_args()

    retriever = HybridRetriever(args.index_dir)
    hits = retriever.retrieve(args.question, final_k=10)
    evs = dedupe_evidence([expand_hit_to_parent(retriever.book_index.nodes, h) for h in hits])
    if args.method == "cross":
        evs = local_cross_encoder_rerank(args.question, evs)
    elif args.method == "llm":
        evs = llm_rerank(args.question, evs)
    print(build_context_block(evs[:5], max_chars=5000))


if __name__ == "__main__":
    main()
