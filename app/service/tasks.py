from app.core.celery_app import celery_app
from app.service.ai_services import QianwenService

@celery_app.task
def process_design_task(design_id, description, garment_type):
    """异步处理AI设计任务"""
    ai_service = QianwenService()
    ai_result = ai_service.parse_design_request(description, garment_type)
    # 更新设计状态（写入数据库或文件）
    return ai_result