#!/bin/bash
# 一键启动 Traffic RAG 系统

set -e
cd "$(dirname "$0")"

echo "=== Traffic RAG 启动脚本 ==="

# 1. 启动基础设施
echo "[1/4] 启动基础设施 (Milvus / Neo4j / Redis)..."
docker-compose up -d milvus-standalone neo4j redis

# 2. 等待容器 healthy
echo "[2/4] 等待容器就绪..."
for i in $(seq 1 30); do
    healthy=$(docker-compose ps --format json 2>/dev/null | grep -c '"healthy"' || true)
    if [ "$healthy" -ge 3 ]; then
        echo "  所有容器已就绪"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  超时！请检查容器状态: docker-compose ps"
        exit 1
    fi
    sleep 2
done

# 3. 初始化数据库（幂等操作，已有数据不会重复创建）
echo "[3/4] 初始化数据库..."
python3 scripts/init_schema.py 2>/dev/null || true

# 4. 启动 API 服务
echo "[4/4] 启动 API 服务..."
export HF_ENDPOINT=https://hf-mirror.com
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > /tmp/rag_api.log 2>&1 &
API_PID=$!
echo "  API PID: $API_PID"

# 等待 API 就绪
echo "  等待 API 启动..."
for i in $(seq 1 60); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo ""
        echo "=== 启动完成 ==="
        echo ""
        echo "  前端页面:   http://localhost:8000/"
        echo "  应急调度:   http://localhost:8000/emergency"
        echo "  数据管理:   http://localhost:8000/admin"
        echo "  API 文档:   http://localhost:8000/docs"
        echo "  健康检查:   http://localhost:8000/health"
        echo "  API 日志:   tail -f /tmp/rag_api.log"
        echo ""
        echo "  关闭命令:   ./stop.sh"
        echo ""
        exit 0
    fi
    printf "."
    sleep 2
done

echo ""
echo "API 启动超时，请检查日志: tail -f /tmp/rag_api.log"
exit 1
