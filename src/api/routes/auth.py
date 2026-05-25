"""认证路由 — 注册 / 登录 / 用户信息."""

import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from passlib.hash import bcrypt
from src.api.middleware.auth import create_access_token, verify_token
from src.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserInfoResponse(BaseModel):
    email: str
    name: str
    clearance_level: int
    stats: dict = {}


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """用户注册."""
    from src.api.main import app_state

    user_store = app_state.get("user_store")
    if not user_store:
        raise HTTPException(status_code=503, detail="用户系统未初始化")

    # 检查邮箱是否已注册
    existing = user_store.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=409, detail="该邮箱已注册")

    # 创建用户
    password_hash = bcrypt.hash(req.password)
    user = user_store.create_user(
        email=req.email, name=req.name, password_hash=password_hash
    )

    # 生成 Token
    token = create_access_token({
        "sub": req.email,
        "name": req.name,
        "clearance_level": user.get("clearance_level", 1),
    })

    logger.info(f"User registered: {req.email}")
    return TokenResponse(
        access_token=token,
        user={"email": req.email, "name": req.name, "clearance_level": user.get("clearance_level", 1)},
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """用户登录."""
    from src.api.main import app_state

    user_store = app_state.get("user_store")
    if not user_store:
        raise HTTPException(status_code=503, detail="用户系统未初始化")

    user = user_store.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    if not bcrypt.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    # 更新登录时间
    user_store.update_last_login(req.email)

    # 生成 Token
    token = create_access_token({
        "sub": req.email,
        "name": user["name"],
        "clearance_level": user.get("clearance_level", 1),
    })

    logger.info(f"User logged in: {req.email}")
    return TokenResponse(
        access_token=token,
        user={"email": req.email, "name": user["name"], "clearance_level": user.get("clearance_level", 1)},
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_me(user: dict = Depends(verify_token)):
    """获取当前用户信息."""
    from src.api.main import app_state

    user_store = app_state.get("user_store")
    if not user_store:
        raise HTTPException(status_code=503, detail="用户系统未初始化")

    db_user = user_store.get_user_by_email(user["user_id"])
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    stats = user_store.get_user_stats(user["user_id"])
    return UserInfoResponse(
        email=db_user["email"],
        name=db_user["name"],
        clearance_level=db_user.get("clearance_level", 1),
        stats=stats,
    )
