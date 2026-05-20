from __future__ import annotations

import argparse
import json
import re


ROUTE_HINTS = {
    "keyword": ["第几", "原文", "在哪", "谁", "何时", "术语", "名称", "定义"],
    "global": ["总结", "概括", "全书", "整体", "主题", "脉络", "框架"],
    "compare": ["比较", "区别", "差异", "不同", "优缺点", "vs", "VS"],
    "graph": ["关系", "实体", "图谱", "GraphRAG", "网络", "影响", "关联"],
    "reasoning": ["为什么", "原因", "如何", "怎么", "机制", "推理"],
}


def route_question(question: str) -> dict:
    """A tiny query router inspired by RAG-Challenge-2 query routing.

    Return knobs rather than a rigid pipeline.
    """
    q = question.strip()
    scores = {route: 0 for route in ROUTE_HINTS}
    for route, words in ROUTE_HINTS.items():
        for w in words:
            if w.lower() in q.lower():
                scores[route] += 1

    route = max(scores, key=scores.get)
    if scores[route] == 0:
        route = "default"

    config = {
        "route": route,
        "use_llm_planner": route in {"compare", "reasoning", "graph", "global"},
        "rerank_method": "cross" if route in {"compare", "reasoning", "graph"} else "none",
        "context_mode": "parent",
        "top_k_per_query": 12,
        "retrieval_k": 24,
        "context_k": 8,
    }
    if route == "keyword":
        config.update({"top_k_per_query": 16, "retrieval_k": 20, "rerank_method": "none"})
    elif route == "global":
        config.update({"retrieval_k": 40, "context_k": 12})
    elif route == "graph":
        config.update({"retrieval_k": 32, "context_k": 10})
    return config


def main() -> None:
    parser = argparse.ArgumentParser("Test query router")
    parser.add_argument("--question", default="总结一下全书关于 GraphRAG 和向量检索的关系")
    args = parser.parse_args()
    print(json.dumps(route_question(args.question), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
