FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# 先复制依赖定义，利用 Docker 缓存层
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# 再复制源码
COPY src/ src/
COPY config/ config/
COPY scripts/ scripts/
COPY rag_information/ rag_information/

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
