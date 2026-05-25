# Traffic RAG — 交通领域 RAG 智能问答系统

基于检索增强生成（RAG）的交通领域智能问答系统，覆盖法规标准精准检索、时空多模态数据接入、涉密数据安全合规、跨路网拓扑关联推理、应急调度多轮对话 5 大核心场景。

---

## 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                   前端 Frontend (React)                   │
│    智能问答 │ 应急调度 │ 数据管理 │ 深色/浅色主题        │
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
│   │   ├── embedders/           #   Embedding 服务（BGE）
│   │   ├── stores/              #   存储（Milvus 向量库 / Neo4j 图库）
│   │   └── pipeline.py          #   离线索引 Pipeline
│   │
│   ├── retrieval_layer/         # 检索层
│   │   ├── retrievers/          #   检索器（法规 / 时空 / GraphRAG）
│   │   ├── rerankers/           #   精排器（Cross-Encoder）
│   │   └── intent_router.py     #   意图路由器（关键词 + LLM 兜底）
│   │
│   ├── generation_layer/        # 生成层
│   │   ├── llm_gateway.py       #   LLM 统一网关（熔断 / Fallback）
│   │   ├── prompt_manager.py    #   Prompt 模板管理
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
├── tests/                       # 测试
│   ├── unit/                    #   单元测试
│   └── integration/             #   集成测试
│
├── rag_information/             # 知识文档（50 份交通领域源文档）
├── data/                        # 数据文件（敏感词库等）
├── .env.example                 # 环境变量模板
├── .gitignore
├── .dockerignore
├── docker-compose.yml           # 开发环境编排
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

### 前置条件

- Python 3.11+
- Node.js 18+（前端开发）
- Docker & Docker Compose
- （可选）NVIDIA GPU — 加速 Embedding 和 Rerank

### 1. 安装依赖

```bash
cd rag_project
pip install -e .          # 生产依赖
pip install -e ".[dev]"   # 开发依赖（含 pytest、ruff）
```

### 2. 配置环境变量

```bash
cp .env.example .env
vim .env
```

必须填写的项：

| 变量 | 说明 | 获取方式 |
|------|------|---------|
| `MIMO_API_KEY` | 小米 MIMO API Key | [小米大模型平台](https://xiaoai.mi.com) |
| `NEO4J_PASSWORD` | Neo4j 数据库密码（至少 8 位） | 自行设置 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 运行 `openssl rand -hex 32` |
| `REDIS_PASSWORD` | Redis 密码 | 自行设置 |

### 3. 启动基础设施

```bash
make infra
# 或手动：
docker-compose up -d milvus-standalone neo4j redis
```

等待所有容器 healthy：

```bash
docker-compose ps
```

### 4. 初始化数据库

```bash
python scripts/init_schema.py
# 创建 Milvus Collection + Neo4j 约束
```

### 5. 批量入库知识文档

```bash
# 国内网络需要设置 HuggingFace 镜像
HF_ENDPOINT=https://hf-mirror.com python scripts/batch_ingest.py
# 解析 rag_information/ 下 50 份 MD 文档
# → 层级切片 → BGE Embedding → 写入 Milvus
```

### 6. 启动 API 服务

```bash
HF_ENDPOINT=https://hf-mirror.com make run
# 或手动：
HF_ENDPOINT=https://hf-mirror.com uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

启动后访问：

| 地址 | 用途 |
|------|------|
| `http://localhost:8000/` | 前端页面（智能问答） |
| `http://localhost:8000/emergency` | 应急调度 |
| `http://localhost:8000/admin` | 数据管理 |
| `http://localhost:8000/docs` | Swagger API 文档 |
| `http://localhost:8000/health` | 健康检查 |

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

### 前端页面

| 路由 | 功能 | 说明 |
|------|------|------|
| `/` | 智能问答 | 聊天式交互，右侧参考来源面板 |
| `/emergency` | 应急调度 | 多轮对话 + 槽位收集进度 + 调度指令生成 |
| `/admin` | 数据管理 | 触发知识文档入库 |

---

## API 接口

所有接口均需 JWT Bearer Token 认证（开发模式下自动跳过）。

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
| 数据层 | Embedding | BAAI/bge-large-zh-v1.5 (1024 维) |
| 数据层 | 向量库 | Milvus 2.4 (HNSW 索引) |
| 数据层 | 图数据库 | Neo4j 5.x |
| 检索层 | Reranker | BAAI/bge-reranker-v2-m3 |
| 生成层 | LLM | MIMO v2.5 (小米大模型，OpenAI 兼容接口) |
| 生成层 | 会话存储 | Redis 7.x |
| 安全层 | 注入防御 | AC 自动机 + 正则检测 |
| 安全层 | PII 脱敏 | 正则匹配 |
| 安全层 | 认证 | JWT Bearer Token |
| API | Web 框架 | FastAPI |
| API | 限流 | Redis 滑动窗口 |

---

## Docker 部署

### 开发环境

```bash
# 启动基础设施
docker-compose up -d milvus-standalone neo4j redis

# 启动 API（本地运行）
HF_ENDPOINT=https://hf-mirror.com uvicorn src.api.main:app --host 0.0.0.0 --port 8000
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

- **JWT 认证**：所有写入接口需 Bearer Token，开发模式自动跳过
- **输入防御**：AhoCorasick 敏感词过滤 + 正则注入检测 + RBAC 权限校验
- **输出脱敏**：手机号、身份证号、车牌号、邮箱自动掩码
- **路径穿越防护**：入库接口校验目录白名单
- **过滤注入防护**：Milvus/Neo4j 查询参数化 + 输入清理
- **熔断降级**：LLM 调用失败自动切换备用 Provider
- **限流**：基于 Redis 的滑动窗口限流（60 次/分钟）

---

## License

MIT
