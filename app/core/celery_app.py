# app/core/celery_app.py（改名后）
from celery import Celery  # 现在可以正确导入Celery库
from app.core.config import settings

# 初始化Celery实例
celery_app = Celery(
    "fashion_ai_tasks",
    broker=settings.CELERY_BROKER_URL,  # 从配置读取Redis地址
    backend=settings.CELERY_BACKEND_URL
)

# 自动发现任务（从service/tasks.py中加载）
celery_app.autodiscover_tasks(["app.service"])