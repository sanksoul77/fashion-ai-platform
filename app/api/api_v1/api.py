# app/api/api_v1/api.py
from fastapi import APIRouter
from app.api import endpoints

api_router = APIRouter()

# 注册AI设计相关接口
api_router.include_router(
    endpoints.router,
    tags=["服装AI设计"]
)