#!/bin/bash
# 一键启动 Traffic RAG 系统

set -e
cd "$(dirname "$0")"

PID_FILE=".rag_api.pid"

echo "=== Traffic RAG 启动脚本 ==="

# 0. 检查是否已启动
if [ -f "$PID_FILE" ]; then
    old_pid=$(cat "$PID_FILE")
    if kill -0 "$old_pid" 2>/dev/null; then
        echo "  API 已在运行 (PID: $old_pid)，请先执行 ./stop.sh"
        exit 1
    fi
    rm -f "$PID_FILE"
fi

# 1. 检测端口冲突
echo "[1/5] 检测端口..."
check_port() {
    local port=$1 name=$2
    if ss -tlnp "sport = :$port" 2>/dev/null | grep -q "LISTEN"; then
        pid=$(sudo ss -tlnp "sport = :$port" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | head -1)
        echo "  错误: 端口 $port ($name) 已被占用 (PID: $pid)"
        echo "  执行 ./stop.sh 清理，或手动停止: sudo kill $pid"
        return 1
    fi
}

port_ok=true
check_port 19530 "Milvus" || port_ok=false
check_port 7687  "Neo4j"  || port_ok=false
check_port 6379  "Redis"  || port_ok=false
check_port 8000  "API"    || port_ok=false

if [ "$port_ok" = false ]; then
    echo ""
    echo "  请先执行 ./stop.sh 清理端口，或手动停止占用进程"
    exit 1
fi
echo "  端口检测通过"

# 2. 启动基础设施
echo "[2/5] 启动基础设施 (Milvus / Neo4j / Redis)..."
docker-compose up -d milvus-standalone neo4j redis

# 3. 等待容器 healthy
echo "[3/5] 等待容器就绪..."
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

# 4. 初始化数据库
echo "[4/5] 初始化数据库..."
if ! python3 scripts/init_schema.py; then
    echo "  数据库初始化失败，请检查错误信息"
    exit 1
fi

# 5. 启动 API 服务
echo "[5/5] 启动 API 服务..."
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > .rag_api.log 2>&1 &
API_PID=$!
echo "$API_PID" > "$PID_FILE"
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
        echo "  API 日志:   tail -f .rag_api.log"
        echo ""
        echo "  关闭命令:   ./stop.sh"
        echo ""
        exit 0
    fi
    printf "."
    sleep 2
done

echo ""
echo "API 启动超时，请检查日志: tail -f .rag_api.log"
exit 1
