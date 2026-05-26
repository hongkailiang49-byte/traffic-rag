#!/bin/bash
# 一键关闭 Traffic RAG 系统

cd "$(dirname "$0")"

PID_FILE=".rag_api.pid"

echo "=== Traffic RAG 关闭脚本 ==="

# 1. 关闭 API 服务
echo "[1/3] 关闭 API 服务..."
if [ -f "$PID_FILE" ]; then
    api_pid=$(cat "$PID_FILE")
    if kill -0 "$api_pid" 2>/dev/null; then
        kill "$api_pid"
        for i in $(seq 1 10); do
            if ! kill -0 "$api_pid" 2>/dev/null; then
                echo "  API 已关闭 (PID: $api_pid)"
                break
            fi
            sleep 1
        done
        if kill -0 "$api_pid" 2>/dev/null; then
            kill -9 "$api_pid" 2>/dev/null
            echo "  API 已强制关闭 (PID: $api_pid)"
        fi
    else
        echo "  API 未在运行"
    fi
    rm -f "$PID_FILE"
else
    echo "  未找到 PID 文件，跳过"
fi

# 2. 清理占用端口的进程
echo "[2/3] 清理占用端口的进程..."
for port in 19530 7687 6379 8000; do
    pid=$(sudo ss -tlnp "sport = :$port" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | head -1)
    if [ -n "$pid" ]; then
        # 不杀 docker-proxy，那是 docker-compose down 管的
        proc_name=$(ps -p "$pid" -o comm= 2>/dev/null)
        if [[ "$proc_name" == "docker-proxy" ]]; then
            continue
        fi
        echo "  端口 $port 被进程 $proc_name (PID: $pid) 占用，正在停止..."
        # 优先用 systemctl 停（防止 systemd 自动重启）
        if sudo systemctl is-active --quiet "$proc_name" 2>/dev/null; then
            sudo systemctl stop "$proc_name" 2>/dev/null
        else
            sudo kill "$pid" 2>/dev/null
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                sudo kill -9 "$pid" 2>/dev/null
            fi
        fi
        echo "  已停止"
    fi
done

# 3. 关闭基础设施
echo "[3/3] 关闭基础设施 (Milvus / Neo4j / Redis)..."
docker-compose down

echo ""
echo "=== 已全部关闭 ==="
echo ""
echo "  如需清除数据库数据: docker-compose down -v"
echo "  重新启动: ./start.sh"
echo ""
