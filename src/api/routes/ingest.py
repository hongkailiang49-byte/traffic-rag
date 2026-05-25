"""数据入库 — /api/v1/ingest."""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from src.api.schemas.query import IngestRequest, IngestResponse
from src.api.middleware.auth import verify_token
from src.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest, user: dict = Depends(verify_token)):
    """触发数据入库."""
    from src.api.main import app_state
    from config.settings import settings

    pipeline = app_state.get("pipeline")
    if not pipeline:
        return IngestResponse(total_files=0, total_chunks=0, success_files=0, failed_files=[], message="系统未初始化")

    data_dir = req.directory or settings.data_dir
    # 路径穿越防护：解析后校验是否在允许的目录下
    resolved = Path(data_dir).resolve()
    allowed_base = Path(settings.data_dir).resolve()
    if not str(resolved).startswith(str(allowed_base)):
        raise HTTPException(status_code=400, detail="不允许访问该目录")
    result = pipeline.run(str(resolved))

    return IngestResponse(
        total_files=result.total_files,
        total_chunks=result.total_chunks,
        success_files=result.success_files,
        failed_files=result.failed_files,
        message=f"入库完成：{result.success_files}/{result.total_files} 文件，{result.total_chunks} 个切片",
    )
