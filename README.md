# Traffic RAG — 交通领域 RAG 智能问答系统

基于检索增强生成（RAG）的交通领域智能问答系统，覆盖法规标准精准检索、时空多模态数据接入、涉密数据安全合规、跨路网拓扑关联推理、应急调度多轮对话 5 大核心场景。

---

## 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                   前端 Frontend (React)                   │
│    智能问答 │ 应急调度 │ 数据管理 │ 会话历史 │ 深色/浅色主题 │
├─────────────────────────────────────────────────────────┤
│                    安全层 Guardrails                     │
│    AC 敏感词 │ 注入检测 │ PII 脱敏 │ RBAC │ JWT         │
├─────────────────────────────────────────────────────────┤
│                   生成层 Generation                      │
│    LLM Gateway (熔断/Fallback) │ Prompt Manager │ Redis │
├─────────────────────────────────────────────────────────┤
│                   检索层 Retrieval                       │
│    Vector Retriever │ Graph Retriever │ Reranker         │
├─────────────────────────────────────────────────────────┤
│                    数据层 Data                           │
│    Parser │ Chunker │ Embedding │ Milvus │ Neo4j        │
└─────────────────────────────────────────────────────────┘
```

## 目录结构

```
rag_project/
├── config/                      # 配置管理
│   └── settings.py              #   Pydantic Settings（环境变量入口）
│
├── src/
│   ├── data_layer/              # 数据层
│   │   ├── parsers/             #   文档解析器（Markdown / PDF / JSON）
│   │   ├── chunkers/            #   切片器（层级切片 / 固定窗口）
│   │   ├── embedders/           #   Embedding 服务（BGE，本地模型）
│   │   ├── stores/              #   存储（Milvus / Neo4j / UserStore）
│   │   └── pipeline.py          #   离线索引 Pipeline
│   │
│   ├── retrieval_layer/         # 检索层
│   │   ├── retrievers/          #   检索器（法规 / 时空 / GraphRAG）
│   │   ├── rerankers/           #   精排器（Cross-Encoder，本地模型）
│   │   └── intent_router.py     #   意图路由器（关键词 + LLM 兜底）
│   │
│   ├── generation_layer/        # 生成层
│   │   ├── llm_gateway.py       #   LLM 统一网关（熔断 / Fallback）
│   │   ├── prompt_manager.py    #   Prompt 模板管理（含身份声明）
│   │   ├── citation.py          #   引用溯源
│   │   └── session/             #   会话管理 + 应急对话状态机
│   │
│   ├── guardrails/              # 安全层
│   │   ├── input_guard.py       #   输入防御（注入检测 / 敏感词 / RBAC）
│   │   └── output_guard.py      #   输出脱敏（PII / 幻觉警告）
│   │
│   ├── api/                     # API 层（FastAPI）
│   │   ├── main.py              #   应用入口 + RAGEngine 编排器
│   │   ├── routes/              #   路由（query / ingest / session）
│   │   ├── middleware/          #   中间件（JWT / 限流）
│   │   └── schemas/             #   Pydantic 请求/响应模型
│   │
│   └── common/                  # 公共工具（日志 / 异常 / 重试）
│
├── models/                      # 本地模型（不提交到 Git）
│   ├── models--BAAI--bge-large-zh-v1.5/    # Embedding 模型
│   └── models--BAAI--bge-reranker-v2-m3/   # Reranker 模型
│
├── frontend/                    # 前端（React + TypeScript）
│   ├── src/
│   │   ├── api/                 #   HTTP 客户端（Axios）
│   │   ├── stores/              #   状态管理（Zustand）
│   │   ├── components/          #   UI 组件
│   │   ├── pages/               #   页面（Chat / Emergency / Admin）
│   │   ├── types/               #   TypeScript 类型定义
│   │   └── constants/           #   常量（应急槽位定义）
│   ├── package.json
│   └── vite.config.ts
│
├── scripts/                     # 运维脚本
│   ├── init_schema.py           #   初始化数据库 Schema
│   ├── batch_ingest.py          #   批量数据入库
│   └── eval_rag.py              #   RAG 效果评测
│
├── start.sh                     # 一键启动脚本（含端口检测 + PID 管理）
├── stop.sh                      # 一键关闭脚本（含端口清理）
├── status.sh                    # 查看系统状态
│
├── tests/                       # 测试
│   ├── unit/                    #   单元测试
│   └── integration/             #   集成测试
│
├── rag_information/             # 知识文档（50 份交通领域源文档）
├── data/                        # 数据文件（敏感词库等）
├── .env.example                 # 环境变量模板
├── .gitignore
├── docker-compose.yml           # 开发环境编排（Milvus / Neo4j / Redis）
├── Dockerfile                   # 容器镜像
├── pyproject.toml               # Python 依赖管理
└── Makefile                     # 常用命令入口
```

## 5 大核心场景

| 场景 | 检索策略 | 关键组件 |
|------|---------|---------|
| **法规标准精准检索** | 向量召回 + 元数据硬过滤 + Cross-Encoder Rerank | `RegulatoryRetriever`、`HierarchicalMarkdownChunker` |
| **时空多模态数据接入** | 向量 + GeoHash 空间过滤 + 时间衰减排序 | `SpatioTemporalRetriever`、`PDFParser`、`JSONParser` |
| **涉密数据安全合规** | 输入端注入检测 + 输出端 PII 脱敏 | `InputGuard`（AC 自动机）、`OutputGuard`（正则脱敏） |
| **跨路网拓扑关联推理** | 向量 + 图遍历双路召回 + 融合 Rerank | `GraphRAGRetriever`、`Neo4jGraphStore` |
| **应急调度多轮对话** | 意图分类 + 槽位提取 + 反问补全 + 状态机 | `EmergencyDialogueManager`、`SessionStore` |

---

## 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| **操作系统** | Ubuntu 20.04+ / macOS / Windows WSL2 | 推荐 Linux |
| **Python** | 3.11+ | 后端运行环境 |
| **Docker** | 24.0+ | 运行 Milvus / Neo4j / Redis |
| **Docker Compose** | v2.0+ | 通常随 Docker Desktop 安装 |
| **Node.js** | 18+ | 构建前端（可选，API 也提供静态文件） |
| **Git** | 2.0+ | 克隆代码 |
| **NVIDIA GPU**（可选） | — | 加速 Embedding 和 Rerank，CPU 也可运行 |

### 1. 克隆代码

```bash
git clone <仓库地址> rag_project
cd rag_project
```

### 2. 创建 Python 虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate   # Linux / macOS
# 或 Windows WSL：
# source venv/bin/activate
```

### 3. 安装 Python 依赖

```bash
pip install --upgrade pip
pip install -e .            # 生产依赖
pip install -e ".[dev]"     # 开发依赖（含 pytest、ruff，可选）
pip install httpx[socks]    # 如需通过代理访问 LLM API
```

### 4. 安装前端依赖并构建

```bash
cd frontend
npm install                 # 安装 Node.js 依赖
npm run build               # 构建生产版本，产物输出到 frontend/dist/
cd ..
```

> 如果没有 Node.js，可以跳过此步骤，API 服务仍可正常运行，但前端页面不可用。

### 5. 配置环境变量

```bash
cp .env.example .env
vim .env   # 填入以下必填项
```

必须填写的项：

| 变量 | 说明 | 获取方式 |
|------|------|---------|
| `MIMO_API_KEY` | 小米 MIMO API Key | [小米大模型平台](https://xiaoai.mi.com) |
| `NEO4J_PASSWORD` | Neo4j 数据库密码（至少 8 位） | 自行设置 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 运行 `openssl rand -hex 32` |
| `REDIS_PASSWORD` | Redis 密码 | 自行设置 |

### 6. 下载模型

Embedding 和 Reranker 模型需要预先下载到 `models/` 目录（详见[模型下载](#模型下载)）：

```bash
pip install huggingface_hub

# 国内用户设置镜像源
export HF_ENDPOINT=https://hf-mirror.com

# 下载 Embedding 模型（约 1.3GB）
huggingface-cli download BAAI/bge-large-zh-v1.5 \
  --local-dir models/models--BAAI--bge-large-zh-v1.5

# 下载 Reranker 模型（约 2.2GB）
huggingface-cli download BAAI/bge-reranker-v2-m3 \
  --local-dir models/models--BAAI--bge-reranker-v2-m3
```

### 7. 启动 Docker 基础设施

```bash
docker-compose up -d milvus-standalone neo4j redis
```

等待所有容器 healthy（首次启动需要拉取镜像，约 2-3 分钟）：

```bash
docker-compose ps   # 确认三个服务都是 healthy
```

### 8. 初始化数据库

```bash
python3 scripts/init_schema.py
```

此脚本会创建：
- Milvus 向量集合 `traffic_knowledge`
- Neo4j 约束（User、Session、交通实体等）

### 9. 批量导入知识文档（可选）

```bash
python3 scripts/batch_ingest.py
```

解析 `rag_information/` 下 50 份交通领域 MD 文档，切片后写入 Milvus。

### 10. 启动 API 服务

```bash
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**或使用一键脚本（推荐，包含端口检测和 PID 管理）**：

```bash
./start.sh
```

`start.sh` 会自动完成：
1. **端口冲突检测** — 检查 19530/7687/6379/8000 是否被占用
2. 启动 Docker 容器（如果未运行）
3. 等待所有容器 healthy
4. 初始化数据库 Schema
5. 启动 API 服务（PID 写入 `.rag_api.pid`）
6. 打印访问地址

### 11. 一键关闭

```bash
./stop.sh
```

`stop.sh` 会：
1. 通过 PID 文件优雅关闭 API 服务
2. 清理占用端口的进程（如系统自带的 Redis）
3. 关闭 Docker 容器

---

### 完整部署流程（一键复制）

```bash
# 1. 克隆代码
git clone https://github.com/hongkailiang49-byte/traffic-rag.git && cd rag_project

# 2. Python 环境
python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip
pip install -e .
pip install httpx[socks]

# 3. 前端构建
cd frontend && npm install && npm run build && cd ..

# 4. 环境变量
cp .env.example .env
# 编辑 .env 填入 MIMO_API_KEY、NEO4J_PASSWORD、JWT_SECRET_KEY、REDIS_PASSWORD

# 5. 下载模型
pip install huggingface_hub
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download BAAI/bge-large-zh-v1.5 --local-dir models/models--BAAI--bge-large-zh-v1.5
huggingface-cli download BAAI/bge-reranker-v2-m3 --local-dir models/models--BAAI--bge-reranker-v2-m3

# 6. 启动
# 前五步第一次需要输入，之后每次输入
# cd rag_project
# source venv/bin/activate 再输入一键启动脚本即可
./start.sh
```

### 访问地址

启动后访问：

| 地址 | 用途 |
|------|------|
| `http://localhost:8000/` | 登录页 / 智能问答 |
| `http://localhost:8000/emergency` | 应急调度 |
| `http://localhost:8000/admin` | 数据管理 |
| `http://localhost:8000/docs` | Swagger API 文档 |
| `http://localhost:8000/health` | 健康检查 |

---

## 用户系统

系统内置了基于 Neo4j 的用户管理，支持注册、登录和用户行为追踪。

### 登录页面

首次访问 `http://localhost:8000/` 会跳转到登录页面，支持：

- **注册**：输入邮箱、姓名、密码（至少 6 位）创建账号
- **登录**：使用已注册的邮箱和密码登录
- **开发模式**：点击"开发模式跳过登录"可快速进入（需先注册一次）

### 用户数据模型

用户信息、会话和聊天记录存储在 Neo4j 图数据库中：

```
(User {email, name, password_hash, clearance_level})
  -[:ASKED]-> (Query {question, intent, created_at})
  -[:HAS_SESSION]-> (Session {session_id, intent, created_at})
       -[:HAS_MESSAGE]-> (ChatMessage {role, content, seq, created_at})
```

- 每次查询自动记录 `(User)-[:ASKED]->(Query)` 关系
- 聊天记录持久化到 Neo4j，支持跨会话保留和历史查询

### 认证机制

- 使用 JWT Bearer Token 认证
- Token 有效期 8 小时（可通过 `JWT_EXPIRE_MINUTES` 配置）
- 开发模式（`APP_ENV=development`）下无 Token 的请求自动以 `dev_user` 身份通过
- 密码使用 bcrypt 哈希存储

---

## 会话管理

登录后左侧边栏显示历史会话列表，支持：

- **新建对话**：点击"新建对话"按钮开始新会话
- **切换会话**：点击历史会话恢复之前的聊天记录
- **删除会话**：hover 会话显示删除按钮，确认后删除
- **自动持久化**：每次对话自动保存到 Neo4j，重启不丢失

---

## 前端开发

前端使用 React + TypeScript + Vite + Tailwind CSS 构建。

### 开发模式（热更新）

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
# API 自动代理到 http://localhost:8000
```

### 构建生产版本

```bash
cd frontend
npm run build
# 构建产物输出到 frontend/dist/
# API 服务会自动提供前端静态文件
```

### 前端技术栈

| 组件 | 选型 |
|------|------|
| 框架 | React 19 + TypeScript |
| 构建 | Vite 8 |
| 样式 | Tailwind CSS 4 |
| 状态管理 | Zustand |
| 路由 | react-router-dom v7 |
| Markdown | react-markdown + remark-gfm + rehype-highlight |
| 图标 | lucide-react |
| UI 组件 | Radix UI（Dialog / ScrollArea / DropdownMenu 等） |

### 前端页面

| 路由 | 功能 | 说明 |
|------|------|------|
| `/login` | 登录/注册 | 用户认证，未登录自动跳转 |
| `/` | 智能问答 | 聊天式交互 + 会话历史侧边栏 + 参考来源面板 |
| `/emergency` | 应急调度 | 多轮对话 + 槽位收集进度 + 调度指令生成 |
| `/admin` | 数据管理 | 触发知识文档入库 |

---

## API 接口

所有接口均需 JWT Bearer Token 认证（开发模式下自动跳过）。

### POST /api/v1/auth/register — 用户注册

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "张三", "password": "123456"}'
```

### POST /api/v1/auth/login — 用户登录

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "123456"}'
```

响应（注册/登录相同）：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {"email": "user@example.com", "name": "张三", "clearance_level": 1}
}
```

### GET /api/v1/auth/me — 获取当前用户信息

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

### POST /api/v1/query — 统一查询

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "公路工程技术标准中对设计速度是怎么规定的？",
    "intent": "auto",
    "top_k": 5
  }'
```

响应：

```json
{
  "answer": "根据《公路工程技术标准》(JTG B01-2014) 第三条规定...",
  "intent": "regulatory",
  "sources": [
    {"content": "...", "score": 0.92, "source": "vector"}
  ],
  "session_id": "a1b2c3d4"
}
```

### GET /api/v1/sessions — 获取会话列表

```bash
curl http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer <token>"
```

响应：

```json
[
  {
    "session_id": "a1b2c3d4",
    "intent": "regulatory",
    "created_at": "2026-05-26T10:30:00",
    "message_count": 4,
    "first_message": "公路工程技术标准中对设计速度是怎么规定的？"
  }
]
```

### GET /api/v1/sessions/{session_id}/messages — 获取会话消息

```bash
curl http://localhost:8000/api/v1/sessions/a1b2c3d4/messages \
  -H "Authorization: Bearer <token>"
```

### DELETE /api/v1/sessions/{session_id} — 删除会话

```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/a1b2c3d4 \
  -H "Authorization: Bearer <token>"
```

### POST /api/v1/session/message — 应急多轮对话

```bash
# 第 1 轮：上报事件
curl -X POST http://localhost:8000/api/v1/session/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "emg001", "message": "京藏高速发生追尾事故"}'

# 第 2 轮：补充信息
curl -X POST http://localhost:8000/api/v1/session/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "emg001", "message": "在清河收费站附近，有人员受伤"}'
```

### POST /api/v1/ingest — 触发数据入库

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"directory": "./rag_information"}'
```

### GET /health — 健康检查

```bash
curl http://localhost:8000/health
# {"status": "ok", "components": {...}}
```

---

## 技术栈

| 层次 | 组件 | 选型 |
|------|------|------|
| 前端 | UI 框架 | React 19 + TypeScript + Vite |
| 前端 | 样式 | Tailwind CSS 4 |
| 前端 | 状态管理 | Zustand |
| 数据层 | Embedding | BAAI/bge-large-zh-v1.5（本地模型，1024 维） |
| 数据层 | 用户存储 | Neo4j（用户 + 会话 + 聊天记录 + 查询行为图） |
| 数据层 | 向量库 | Milvus 2.4 (HNSW 索引) |
| 数据层 | 图数据库 | Neo4j 5.x |
| 检索层 | Reranker | BAAI/bge-reranker-v2-m3（本地模型） |
| 生成层 | LLM | MIMO v2.5（小米大模型，OpenAI 兼容接口） |
| 生成层 | 会话存储 | Redis 7.x（热数据） + Neo4j（持久化） |
| 安全层 | 注入防御 | AC 自动机 + 正则检测 |
| 安全层 | PII 脱敏 | 正则匹配 |
| 安全层 | 认证 | JWT Bearer Token |
| API | Web 框架 | FastAPI |
| API | 限流 | Redis 滑动窗口 |

---

## 模型下载

Embedding 和 Reranker 模型存放在 `models/` 目录下，从本地加载，无需运行时联网。模型目录已在 `.gitignore` 中排除，需要手动下载。

### 方式一：使用 huggingface-cli（推荐）

```bash
# 安装 huggingface_hub
pip install huggingface_hub

# 国内用户设置镜像源
export HF_ENDPOINT=https://hf-mirror.com

# 下载 Embedding 模型
huggingface-cli download BAAI/bge-large-zh-v1.5 \
  --local-dir models/models--BAAI--bge-large-zh-v1.5

# 下载 Reranker 模型
huggingface-cli download BAAI/bge-reranker-v2-m3 \
  --local-dir models/models--BAAI--bge-reranker-v2-m3
```

### 方式二：使用 Python 脚本

```python
from huggingface_hub import snapshot_download
import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 国内镜像

# Embedding 模型
snapshot_download(
    "BAAI/bge-large-zh-v1.5",
    local_dir="models/models--BAAI--bge-large-zh-v1.5",
)

# Reranker 模型
snapshot_download(
    "BAAI/bge-reranker-v2-m3",
    local_dir="models/models--BAAI--bge-reranker-v2-m3",
)
```

### 方式三：Git LFS

```bash
# 需要先安装 git-lfs
git lfs install

# Embedding 模型
git clone https://huggingface.co/BAAI/bge-large-zh-v1.5 \
  models/models--BAAI--bge-large-zh-v1.5

# Reranker 模型
git clone https://huggingface.co/BAAI/bge-reranker-v2-m3 \
  models/models--BAAI--bge-reranker-v2-m3
```

### 目录结构验证

下载完成后，`models/` 目录应如下：

```
models/
├── models--BAAI--bge-large-zh-v1.5/
│   ├── snapshots/
│   │   └── 79e7739b6ab944e86d6171e44d24c997fc1e0116/
│   │       ├── config.json
│   │       ├── model.safetensors
│   │       ├── tokenizer.json
│   │       └── ...
│   └── ...
└── models--BAAI--bge-reranker-v2-m3/
    ├── snapshots/
    │   └── 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e/
    │       ├── config.json
    │       ├── model.safetensors
    │       ├── tokenizer.json
    │       └── ...
    └── ...
```

> **注意**：如果使用 `huggingface-cli download` 加了 `--local-dir`，目录结构可能不同。
> 系统通过 `config/settings.py` 中的路径加载模型，如需自定义路径，设置环境变量：
> ```bash
> EMBEDDING_MODEL=/your/path/to/bge-large-zh-v1.5
> RERANKER_MODEL=/your/path/to/bge-reranker-v2-m3
> ```

---

## Docker 部署

### 开发环境

```bash
# 启动基础设施
docker-compose up -d milvus-standalone neo4j redis

# 启动 API（本地运行）
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 生产环境

```bash
# 构建前端
cd frontend && npm run build && cd ..

# 构建 Docker 镜像
docker build -t traffic-rag .

# 运行
docker run -d \
  --env-file .env \
  -p 8000:8000 \
  --network rag_project_default \
  traffic-rag
```

---

## 测试

```bash
# 运行全部测试
make test

# 运行特定测试
pytest tests/unit/test_chunkers.py -v

# 查看覆盖率
pytest tests/ --cov=src --cov-report=html
```

## 评测

```bash
python scripts/eval_rag.py
# 输出：
#   Recall@10: 0.XXX (target: ≥ 0.90)
#   MRR@5:     0.XXX (target: ≥ 0.80)
```

| 评测维度 | 指标 | 目标值 |
|---------|------|-------|
| 检索质量 | Recall@10 | ≥ 0.90 |
| 检索质量 | MRR@5 | ≥ 0.80 |
| 生成质量 | Faithfulness | ≥ 0.85 |
| 安全性 | 注入拦截率 | ≥ 0.95 |
| 安全性 | PII 脱敏召回率 | ≥ 0.99 |

---

## 安全特性

- **用户认证**：注册/登录 + JWT Bearer Token，密码 bcrypt 哈希存储
- **JWT 认证**：所有写入接口需 Bearer Token，开发模式自动跳过
- **输入防御**：AhoCorasick 敏感词过滤 + 正则注入检测 + RBAC 权限校验
- **输出脱敏**：手机号、身份证号、车牌号、邮箱自动掩码
- **路径穿越防护**：入库接口校验目录白名单
- **过滤注入防护**：Milvus/Neo4j 查询参数化 + 输入清理
- **熔断降级**：LLM 调用失败自动切换备用 Provider
- **限流**：基于 Redis 的滑动窗口限流（60 次/分钟）
- **身份声明**：系统自称为交通领域智能问答系统，不暴露底层模型信息

---

## License

MIT
