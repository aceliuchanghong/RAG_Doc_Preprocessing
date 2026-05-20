# RAG_Doc_Preprocessing

RAG 项目真正决定上限的，往往不是“向量检索算法”，而是“文档预处理和索引结构”。

## install

```bash
cp .env.example .env
uv run install.py
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
