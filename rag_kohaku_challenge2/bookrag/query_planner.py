from __future__ import annotations

import argparse
import json
import os
import re


def simple_query_plan(question: str, max_queries: int = 4) -> list[str]:
    """Cheap query expansion.

    For production, you can replace this with an LLM planner.
    """
    q = question.strip()
    queries = [q]
    cleaned = re.sub(r"(请问|什么是|如何|怎么|为什么|是否|请解释|解释一下|总结|概括)", " ", q)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned and cleaned != q:
        queries.append(cleaned)
    if any(x in q for x in ["原因", "为什么", "为何"]):
        queries.append(q + " 原因 背景 机制 影响")
    if any(x in q for x in ["比较", "区别", "差异", "不同"]):
        queries.append(q + " 对比 差异 优缺点")
    if any(x in q for x in ["定义", "是什么", "概念"]):
        queries.append(q + " 定义 概念 含义")
    if any(x.lower() in q.lower() for x in ["graph", "图谱", "关系", "实体"]):
        queries.append(q + " 实体 关系 图 社区 摘要")

    seen, out = set(), []
    for item in queries:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out[:max_queries]


def llm_query_plan(question: str, max_queries: int = 4, model: str = "gpt-4o-mini") -> list[str]:
    if not os.getenv("OPENAI_API_KEY"):
        return simple_query_plan(question, max_queries=max_queries)

    try:
        from openai import OpenAI
        client = OpenAI()
        prompt = f"""
你是 RAG query planner。把问题改写成最多 {max_queries} 个检索查询。
要求：保留原问题；补充同义词；复合问题拆成子问题；输出 JSON。
格式：{{"queries": ["...", "..."]}}
问题：{question}
"""
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        queries = [x.strip() for x in data.get("queries", []) if isinstance(x, str) and x.strip()]
        if question not in queries:
            queries.insert(0, question)
        return queries[:max_queries]
    except Exception as e:
        print("LLM planner failed, fallback:", e)
        return simple_query_plan(question, max_queries=max_queries)


def main() -> None:
    parser = argparse.ArgumentParser("Test query planner")
    parser.add_argument("--question", default="GraphRAG 和向量检索有什么区别？")
    parser.add_argument("--llm", action="store_true")
    args = parser.parse_args()
    queries = llm_query_plan(args.question) if args.llm else simple_query_plan(args.question)
    print(json.dumps(queries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
