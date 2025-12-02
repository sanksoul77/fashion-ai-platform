import os
import sys
import warnings
from pathlib import Path

# -------------------------- 修复模块路径 + 屏蔽无用警告 --------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

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

# -------------------------- 初始化FastAPI --------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=None,
    redoc_url="/redoc"
)


# -------------------------- 手动替换Swagger CDN --------------------------
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],  # 明确指定前端开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------- 目录创建和静态文件服务 --------------------------
# 确保上传目录存在
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"✅ 上传目录已创建: {settings.UPLOAD_DIR}")
except PermissionError as e:
    print(f"❌ 无权限创建上传目录: {e}")
    raise RuntimeError(f"无权限创建上传目录：{settings.UPLOAD_DIR}")
except Exception as e:
    print(f"⚠️ 创建上传目录时出现警告: {e}")

# 创建静态图片目录（用于默认图片）
static_images_dir = Path("static/images")
static_images_dir.mkdir(parents=True, exist_ok=True)

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

print(f"✅ 静态文件服务已配置:")
print(f"   - 上传目录: /uploads -> {settings.UPLOAD_DIR}")
print(f"   - 静态文件: /static -> ./static")

# -------------------------- 注册API路由 --------------------------
app.include_router(api_router, prefix=settings.API_V1_STR)


# -------------------------- 根路径和健康检查接口 --------------------------
@app.get("/")
async def root():
    return {
        "message": "欢迎使用服装定制AI平台",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_check": "/api/v1/health",
        "endpoints": {
            "products": "/api/v1/products",
            "ai_chat": "/api/v1/ai/chat",
            "design": "/api/v1/ai-design"
        }
    }


@app.get("/api/status")
async def api_status():
    """API状态检查"""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": settings.VERSION
    }


# -------------------------- 启动入口 --------------------------
if __name__ == "__main__":
    import uvicorn
    from datetime import datetime

    print("=" * 60)
    print("🚀 服装定制AI平台后端服务启动中...")
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 服务地址: http://localhost:8000")
    print(f"📚 API文档: http://localhost:8000/docs")
    print(f"📁 上传目录: {settings.UPLOAD_DIR}")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )