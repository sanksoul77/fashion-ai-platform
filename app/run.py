import uvicorn
from fastapi import FastAPI
import fastapi_cdn_host  # 新增：导入CDN替换库

# 导入你的路由（后续步骤会补，先加这行）
from app.api.endpoints import router as api_router

# 创建FastAPI实例
app = FastAPI(
    title="Fashion AI Platform",  # 可选：给文档加标题
    description="时尚AI平台API文档",
    version="1.0.0"
)

# 新增：替换Swagger UI的CDN为国内源
fastapi_cdn_host.patch_docs(app)

# 新增：挂载接口路由（解决接口未注册问题）
app.include_router(api_router, prefix="/api", tags=["API接口"])

# 健康检查接口（可选：加一个测试接口）
@app.get("/api/health", tags=["健康检查"])
def health_check():
    return {"status": "ok", "message": "服务正常运行"}

if __name__ == "__main__":
    uvicorn.run("app.run:app", host="0.0.0.0", port=8000, reload=True)