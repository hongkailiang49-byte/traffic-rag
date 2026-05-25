"""JWT 认证中间件."""

from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from config.settings import settings
from src.common.logger import get_logger

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not set. Generate one with: openssl rand -hex 32")
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    """验证 JWT Token，返回用户上下文."""
    if not credentials:
        # 开发模式允许无 Token
        if settings.app_env == "development":
            logger.warning("Auth bypassed: running in development mode without token")
            return {"user_id": "dev_user", "clearance_level": 1}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    if not settings.jwt_secret_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT_SECRET_KEY not configured")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return {
            "user_id": payload.get("sub", "unknown"),
            "clearance_level": payload.get("clearance_level", 1),
        }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
