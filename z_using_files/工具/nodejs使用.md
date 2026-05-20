1. 去官网下载 `nodejs`

2. 执行npm

```bash
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
npm install -g @anthropic-ai/claude-code

npm install -g npm@11.14.1
```

| 维度 | JavaScript 生态 | Python 生态 | 形象理解 |
| --- | --- | --- | --- |
| **运行时 (Runtime)** | **Node.js** | **Python Interpreter** | 解释并运行代码的“大脑” |
| **包管理器 (Package Manager)** | **npm** | **pip** / **conda** | 搬运和安装第三方插件的“搬运工” |
| **仓库 (Registry)** | **npmjs.com** | **PyPI** (Python Package Index) | 存放成千上万代码包的“大仓库” |

| 工具 | 对应 Python 概念 | 行为模式 |
| --- | --- | --- |
| **npm** | **pip** | **安装**工具。把包下载到硬盘里，供以后使用。 |
| **npx** | **pipx** (或 `python -m`) | **执行**工具。它会去远程仓库找这个包，下载并直接运行其命令，但不会把这个包永久留在你的电脑里。 |


3. 查看 claude 版本
```bash
claude --version
```

4. 配置环境变量
```bash
# linux
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=<API Key>
export ANTHROPIC_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
export CLAUDE_CODE_EFFORT_LEVEL=max

# powershell
# https://api-docs.deepseek.com/zh-cn/guides/agent_integrations/claude_code
$env:ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
$env:ANTHROPIC_AUTH_TOKEN="<API Key>"
$env:ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"
$env:CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
$env:CLAUDE_CODE_EFFORT_LEVEL="max"
```

5. 进入项目目录，执行 claude 命令，即可开始使用了。

```bash
cd /path/to/my-project
claude
```

| JS 概念 | Python 对应物 | 解释 (以 Python 视角) |
| --- | --- | --- |
| **npm** | **pip** | 官方标准的包管理器，负责下载和管理依赖。 |
| **cnpm** | **国内镜像源 (如清华/阿里源)** | npm 的中国镜像版。以前 npm 下载慢，大家用 cnpm；现在通常推荐给 npm 配置国内 registry 镜像，或者用 `pnpm`。 |
| **fnm / nvm** | **pyenv / conda** | **Node 版本管理器**。Python 有 3.8/3.11 之分，Node 也有 v18/v20/v22。fnm 让你能一键切换 Node 版本。 |
| **TypeScript (ts)** | **Type Hints + Mypy** | 为 JavaScript 加上**强类型**。就像在 Python 里写 `name: str = "Gemini"` 并用工具强制检查一样，TS 让代码更健壮。 |
| **Vite** | **Poetry / PyInstaller / Flask 实时重载** | **构建工具**。它负责把你的 TS/JS 代码快速打包、热更新。比以前的 Webpack 快得多，类似一个极速的开发服务器 + 打包器。 |
| **package.json** | **requirements.txt / pyproject.toml** | 声明项目依赖、版本号和运行脚本的地方。 |

### 一个典型的开发流对比

如果要开始一个新项目：

* **Python 流程：**
1. `pyenv local 3.11` (选版本)
2. `python -m venv venv` (建环境)
3. `pip install flask` (装库)
4. `python app.py` (运行)


* **Modern JS 流程 (Vite + TS)：**
1. `fnm use 20` (选版本)
2. `npm create vite@latest` (初始化项目，类似 Django/FastAPI 的脚手架)
3. `npm install` (安装 `package.json` 里的库)
4. `npm run dev` (启动 Vite 开发服务器)
