# RAG_Doc_Preprocessing

  ▎ RAG 项目真正决定上限的，往往不是“向量检索算法”，而是“文档预处理和索引结构”。

  传统 RAG 系统普遍采用简单的"固定窗口切片 + 向量化"方案，存在三大核心缺陷：

  1. 语义粒度丢失 — 机械切片破坏段落的上下文完整性，检索到的片段缺少前后文
  2. 结构信息丢弃 — 忽略了文档固有的章、节、段层级关系，无法做父子回溯
  3. 多维度检索缺失 — 仅靠单一稠密向量，无法同时覆盖精确匹配（BM25）、实体关联（GraphRAG）、全局概览（RAPTOR 摘要）

  本项目设计了一套融合式文档预处理管线，在数据进入向量库之前就完成层次化解析、知识图谱实体标注、层级摘要生成和自底向上向量聚合，从根本上提升 RAG 系统的召回质量。

```
  原始文档
    │
    ▼
  ┌────────────────────────────────────────────────────┐
  │  Stage 1: Parser — 四层语义树切分 + 时序编码          │
  │                                                     │
  │  Document → Section(章节) → Paragraph(段落) → Sentence(句子) │
  │                                                     │
  │  每个节点携带 chronological_progress (0.0~1.0)，     │
  │  表示该文本在全文中的绝对时间线位置                     │
  └──────────────────────┬──────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────┐
  │  Stage 2: Analyzer — GraphRAG-Light + RAPTOR         │
  │                                                     │
  │  • GraphRAG-Light: 对每个句子提取命名实体标签          │
  │  • RAPTOR: 自底向上生成段落摘要、章节宏观摘要          │
  │    （生产环境替换为 LLM API 调用）                     │
  └──────────────────────┬──────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────┐
  │  Stage 3: Embedder — Kohaku 自底向上加权聚合          │
  │                                                     │
  │  1. 仅对最底层句子计算原始 embedding                   │
  │  2. 段落向量 = Σ(子句向量 × 句子长度权重)             │
  │  3. 章节向量 = Σ(子段落向量 × 段落长度权重)            │
  │  4. 额外为 RAPTOR 摘要生成独立语义向量                 │
  └──────────────────────┬──────────────────────────────┘
                         ▼
  ┌─────────────────────────────────────────────────────┐
  │  Stage 4: Flatten — RAG-Challenge-2 高密度 Payload   │
  │                                                     │
  │  以句子为最小检索单元打平输出，每条记录包含：            │
  │  • 句子自身向量 + 文本 + 实体标签 + 时序进度            │
  │  • 冗余绑定父段落全文（召回句子 → 返回完整段落上下文）   │
  │  • 父段落 RAPTOR 摘要及其向量                          │
  │  • 父章节标题 + 章节摘要 + 章节摘要向量                 │
  │  → 可直接写入 FAISS / Milvus 等向量数据库              │
  └─────────────────────────────────────────────────────┘
                         │
                         ▼  (下游消费)
  ┌─────────────────────────────────────────────────────┐
  │  检索侧: HybridRetriever (Dense + BM25 + RRF 融合)   │
  │  → 多查询扩展 → 父文档回溯 → Rerank → 结构化问答       │
  └─────────────────────────────────────────────────────┘
```
  关键设计：

  - 父子回溯：以句子为检索单元命中，但通过 context_metadata 直接拿到完整段落甚至章节的上下文，解决"碎片化召回"问题
  - Kohaku 加权聚合：上层节点的向量不是独立计算的，而是由子节点按文本长度加权平均聚合，保证语义连贯且节省计算
  - 时序进度编码：每个节点携带 [0.0, 1.0] 的全文位置，检索时可利用位置信息做时间线相关的排序过滤
  - 检索侧多路融合：Dense 向量 + BM25 稀疏检索 → Reciprocal Rank Fusion (RRF) 合并排序，兼顾语义相似和精确匹配


## install

```bash
cp .env.example .env
uv sync --default-index "https://pypi.tuna.tsinghua.edu.cn/simple"
```

## 开发规范

### Commit 提交规范

Angular 规范格式：`<type>(<scope>): <subject>`

| Type (类型) | 含义说明 | 示例 |
| :--- | :--- | :--- |
| `feat` | 新增一个业务或功能 | `feat(ai): 新增混合检索重排策略` |
| `fix` | 修复一个 Bug | `fix(auth): 修复高并发下 Token 刷新竞态问题` |
| `refactor` | 重构 (非新增也非修复) | `refactor(billing): 将计费核心逻辑下沉到 Service` |
| `docs` | 文档修改 | `docs(readme): 更新项目本地部署指南` |
| `perf` | 性能优化 | `perf(rag): 将单条嵌入优化为批量向量化` |
| `chore` | 构建、依赖或配置变动 | `chore(deps): 升级 Spring AI 到 1.0 正式版` |
| `test` | 补充或修改测试代码 | `test(chat): 补充流式对话接口的端到端单测` |

### 代码格式化规范
  - 强制使用 **black-formatter (Black)** 作为代码格式化工具 (Line length = 88)。确保团队代码风格高度一致，减少无谓的 Code Review 格式争议。
  - 强制使用 **isort** 对 import 语句进行排序和分组。
  - 强制使用 **Ruff** (或 Flake8) 作为代码静态检查工具，必须通过 CI 流水线的 Lint 检查阶段。
  - **强制 Type Hints (类型注解):** 所有核心业务函数、API 路由处理函数必须包含完整的类型注解（包括入参和返回值类型）。
     - *正确示例:* `def get_user(user_id: int) -> UserResponse:`

### 开发环境与依赖管理
- 使用 uv 作为包管理工具, 统一管理虚拟环境（Venv）与依赖包。

| 常用操作 | 功能描述 | 示例命令 |
| :--- | :--- | :--- |
| **初始化环境** | 在当前目录创建高性能虚拟环境 | `uv venv` |
| **安装依赖** | 极速安装并同步依赖至 `pyproject.toml` | `uv add "fastapi>=0.110.0"` |

### Docker 容器构建最佳实践
为了加速构建并控制镜像大小，必须使用依赖分离多阶段构建。

```dockerfile
# 基础镜像使用 Slim 版本
FROM python:3.11-slim AS requirements-stage

WORKDIR /tmp
# 安装 Poetry
RUN pip install poetry
COPY ./pyproject.toml ./poetry.lock* /tmp/
# 导出 requirements.txt 以利用 Docker 构建缓存
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.11-slim

WORKDIR /app
COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt
# 生产环境安装，禁用 pip 缓存减小体积
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app/app
COPY ./prompts /app/prompts

# 使用非 root 用户
RUN useradd -m myuser
USER myuser

# Uvicorn 启动
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
