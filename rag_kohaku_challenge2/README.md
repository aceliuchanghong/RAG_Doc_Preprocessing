# rag_kohaku_challenge2

教学项目：把 KohakuRAG 的层级文档预处理，和 RAG-Challenge-2 的 parent retrieval / rerank / structured answer 思路结合起来，用于 `book.txt`。

## 安装

```bash
pip install -r requirements.txt
```

## 建索引

```bash
python -m bookrag.index_store --book book.txt --index-dir data/book_index
# 或
PYTHONPATH=. python scripts/index_book.py --book book.txt --index-dir data/book_index
```

## 检索测试

```bash
python -m bookrag.retrieval --index-dir data/book_index --question "GraphRAG 和向量检索有什么区别？"
```

## 上下文扩展测试

```bash
python -m bookrag.context --index-dir data/book_index --question "parent retrieval 是什么？" --mode parent
python -m bookrag.context --index-dir data/book_index --question "parent retrieval 是什么？" --mode window
```

## 问答

不设置 `OPENAI_API_KEY` 时，只会返回证据预览，不会真的生成答案。

```bash
export OPENAI_API_KEY="你的key"
python -m bookrag.answer --index-dir data/book_index --question "GraphRAG 和普通向量检索有什么区别？" --rerank cross
```

## 每个文件的 main 测试

```bash
python -m bookrag.schema
python -m bookrag.text_utils
python -m bookrag.preprocess --book book.txt --out data/nodes.json
python -m bookrag.embeddings --nodes data/nodes.json --out data/embeddings.npz
python -m bookrag.index_store --book book.txt --index-dir data/book_index
python -m bookrag.query_planner --question "GraphRAG 和向量检索有什么区别？"
python -m bookrag.retrieval --index-dir data/book_index --question "GraphRAG 和向量检索有什么区别？"
python -m bookrag.context --index-dir data/book_index --question "parent retrieval 是什么？"
python -m bookrag.rerank --index-dir data/book_index --question "GraphRAG 适合什么问题？" --method cross
python -m bookrag.answer --index-dir data/book_index --question "GraphRAG 和向量检索有什么区别？"
python -m bookrag.router --question "总结一下全书关于 GraphRAG 的脉络"
python -m bookrag.graphlite --nodes data/book_index/nodes.json --query "GraphRAG 和向量检索的关系"
python -m bookrag.raptorlite --nodes data/book_index/nodes.json --out data/nodes_with_raptor.json
python -m bookrag.eval --index-dir data/book_index --qa data/qa.jsonl
```

## 模块说明

- `preprocess.py`: book.txt -> document / section / paragraph / sentence tree
- `embeddings.py`: sentence embedding + parent bottom-up aggregation
- `index_store.py`: FAISS + BM25 index
- `query_planner.py`: multi-query planner
- `retrieval.py`: dense + BM25 + RRF hybrid retrieval
- `context.py`: parent retrieval / sentence window expansion
- `rerank.py`: local cross-encoder rerank / optional LLM rerank
- `answer.py`: structured answer + abstention-aware voting
- `router.py`: question router, dynamically choose knobs
- `graphlite.py`: lightweight GraphRAG-like term graph
- `raptorlite.py`: RAPTOR-like cluster summary layer
- `eval.py`: recall@k / MRR evaluation
