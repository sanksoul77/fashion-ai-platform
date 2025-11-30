# app/db/models.py
from sqlalchemy import Column, String, JSON, DateTime, Enum
from datetime import datetime
from app.db.base import Base
import enum

class DesignStatus(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DesignTask(Base):
    __tablename__ = "design_tasks"
    design_id = Column(String, primary_key=True, index=True)
    task_id = Column(String)  # Celery任务ID
    description = Column(String)
    garment_type = Column(String)
    image_path = Column(String)  # 图片存储路径
    spec = Column(JSON)  # AI生成的设计规格
    status = Column(Enum(DesignStatus), default=DesignStatus.PROCESSING)
    created_at = Column(DateTime, default=datetime.utcnow)