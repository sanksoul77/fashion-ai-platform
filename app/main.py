import os
import sys
import warnings

# -------------------------- 修复模块路径 + 屏蔽无用警告 --------------------------
# 1. 将项目根目录加入Python搜索路径（解决ModuleNotFound）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# 2. 屏蔽transformers的框架检查警告（暂时不用AI模型时）
warnings.filterwarnings("ignore", message="None of PyTorch, TensorFlow >= 2.0, or Flax have been found.")

# -------------------------- 核心依赖导入 --------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)

from app.api.api_v1.api import api_router
from app.core.config import settings

# -------------------------- 初始化FastAPI + 手动替换Swagger CDN（替代fastapi_cdn_host） --------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    # 关闭默认docs，手动实现（用于替换CDN）
    docs_url=None,
    redoc_url="/redoc"
)

# 手动实现Swagger UI，替换为国内CDN（解决原fastapi_cdn_host失效问题）
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        # 替换Swagger UI的CSS/JS为国内源
        swagger_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.10.3/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.10.3/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

# -------------------------- CORS跨域配置 --------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境替换为具体前端域名（如["http://localhost:3000"]）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------- 上传目录创建 + 静态文件挂载 --------------------------
# 创建上传目录（添加权限错误处理）
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except PermissionError:
    raise RuntimeError(f"无权限创建上传目录：{settings.UPLOAD_DIR}")

# 挂载静态文件目录（适配绝对路径）
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# -------------------------- 注册API路由 --------------------------
app.include_router(api_router, prefix=settings.API_V1_STR)

# -------------------------- 根路径接口 --------------------------
@app.get("/")
async def root():
    return {
        "message": "欢迎使用服装定制AI平台",
        "docs_url": "/docs",  # 手动替换后的Swagger地址
        "version": settings.VERSION
    }

# -------------------------- 启动入口 --------------------------
if __name__ == "__main__":
    import uvicorn
    # 从项目根目录启动（推荐方式）
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        # 屏蔽uvicorn的冗余日志（可选）
        log_level="info"
    )