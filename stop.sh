#!/bin/bash
# 一键关闭 Traffic RAG 系统

cd "$(dirname "$0")"

echo "=== Traffic RAG 关闭脚本 ==="

# 1. 关闭 API 服务
echo "[1/2] 关闭 API 服务..."
pkill -f "uvicorn src.api.main:app" 2>/dev/null && echo "  API 已关闭" || echo "  API 未在运行"

# 2. 关闭基础设施
echo "[2/2] 关闭基础设施 (Milvus / Neo4j / Redis)..."
docker-compose down

echo ""
echo "=== 已全部关闭 ==="
echo ""
echo "  如需清除数据库数据: docker-compose down -v"
echo "  重新启动: ./start.sh"
echo ""
