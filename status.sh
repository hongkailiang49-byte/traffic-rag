#!/bin/bash
# 查看 Traffic RAG 系统状态

cd "$(dirname "$0")"

echo "=== Traffic RAG 系统状态 ==="
echo ""

# 基础设施
echo "基础设施:"
docker-compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  docker-compose 未运行"
echo ""

# API 服务
echo "API 服务:"
if pgrep -f "uvicorn src.api.main:app" > /dev/null 2>&1; then
    PID=$(pgrep -f "uvicorn src.api.main:app")
    echo "  运行中 (PID: $PID)"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  健康检查: OK"
    else
        echo "  健康检查: 未响应"
    fi
else
    echo "  未运行"
fi
echo ""

echo "快速命令:"
echo "  启动: ./start.sh"
echo "  关闭: ./stop.sh"
echo "  日志: tail -f /tmp/rag_api.log"
echo ""
