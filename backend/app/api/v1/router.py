"""
API路由汇总
"""
from fastapi import APIRouter
from app.api.v1.endpoints import detection

api_router = APIRouter()

# 注册检测相关路由
api_router.include_router(
    detection.router,
    prefix="/detection",
    tags=["Detection"]
)
