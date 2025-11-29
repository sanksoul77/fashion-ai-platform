from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS（允许Vue前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)

# 挂载静态文件
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "服装定制AI平台后端服务运行中"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "fashion-ai-backend"}

from app.api.endpoints import router as api_router

app.include_router(api_router, prefix=settings.API_V1_STR)

