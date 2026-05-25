# 交通领域 RAG 系统架构说明

## 目录结构

```
traffic-rag/
├── config/          # 配置管理
├── src/
│   ├── data_layer/      # 数据层（解析、切片、Embedding、存储）
│   ├── retrieval_layer/ # 检索层（检索器、Reranker、意图路由）
│   ├── generation_layer/# 生成层（LLM Gateway、Prompt、Session）
│   ├── guardrails/      # 安全层（输入防御、输出脱敏）
│   ├── api/             # API 层（FastAPI 路由、中间件）
│   └── common/          # 公共工具
├── scripts/         # 运维脚本
├── tests/           # 测试
└── docs/            # 文档
```

## 依赖关系

```
api → generation_layer → retrieval_layer → data_layer
         ↘ guardrails ↙
```

## 启动流程

1. `make infra` — 启动 Milvus + Neo4j + Redis
2. `python scripts/init_schema.py` — 初始化数据库 Schema
3. `python scripts/batch_ingest.py` — 批量入库 50 份知识文档
4. `make run` — 启动 API 服务 (http://localhost:8000)

## API 接口

- `POST /api/v1/query` — 统一查询
- `POST /api/v1/ingest` — 触发入库
- `POST /api/v1/session/message` — 应急对话
- `GET /health` — 健康检查
- `GET /docs` — Swagger 文档
