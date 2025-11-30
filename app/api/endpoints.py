import os
import uuid
import logging
from datetime import datetime
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.models import DesignTask, DesignStatus
from app.service.tasks import process_design_task  # 从tasks.py导入Celery异步任务
from app.service.ai_services import QianwenService  # 导入AI服务类

# 配置日志
logger = logging.getLogger("fashion_ai.endpoints")
logger.setLevel(logging.INFO)

router = APIRouter()

# 允许的文件类型和大小限制（从配置读取）
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]
MAX_FILE_SIZE_MB = settings.MAX_FILE_SIZE // 1024 // 1024


@router.get("/health")
async def health_check():
    """服务健康检查接口，返回基础配置信息"""
    # 检查上传目录可访问性
    is_upload_dir_accessible = False
    try:
        if not os.path.exists(settings.UPLOAD_DIR):
            os.makedirs(settings.UPLOAD_DIR)
        # 测试写入权限
        test_file = os.path.join(settings.UPLOAD_DIR, ".test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        is_upload_dir_accessible = True
    except Exception as e:
        logger.error(f"上传目录不可访问: {str(e)}")

    return JSONResponse({
        "code": 200,
        "message": "服务正常",
        "data": {
            "status": "ok",
            "version": settings.VERSION,
            "upload_dir": settings.UPLOAD_DIR,
            "upload_dir_accessible": is_upload_dir_accessible,
            "file_limit": {
                "max_size_mb": MAX_FILE_SIZE_MB,
                "allowed_types": ALLOWED_CONTENT_TYPES
            }
        }
    })


@router.get("/meta-info")
async def get_meta_info():
    """返回前端所需的元数据（枚举值、选项等）"""
    return JSONResponse({
        "code": 200,
        "message": "success",
        "data": {
            "garment_types": [
                {"value": "dress", "label": "连衣裙"},
                {"value": "shirt", "label": "衬衫"},
                {"value": "pants", "label": "裤子"},
                {"value": "coat", "label": "外套"},
                {"value": "tshirt", "label": "T恤"}
            ],
            "design_status": [
                {"value": "processing", "label": "处理中"},
                {"value": "completed", "label": "已完成"},
                {"value": "failed", "label": "失败"}
            ]
        }
    })


@router.post("/ai-design")
async def create_ai_design(
        description: str = Form(..., description="设计需求描述"),
        garment_type: str = Form(..., description="服装类型（参考/meta-info接口）"),
        model_image: UploadFile = File(..., description="参考图片（JPG/PNG）"),
        db: Session = Depends(get_db)
):
    """提交AI设计任务（异步处理）"""
    try:
        # 1. 验证文件类型
        if model_image.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"文件类型不支持，仅允许: {ALLOWED_CONTENT_TYPES}"
            )

        # 2. 验证文件大小
        content = await model_image.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（最大{MAX_FILE_SIZE_MB}MB）"
            )

        # 3. 处理图片（压缩+保存）
        design_id = f"design_{uuid.uuid4().hex[:10]}"  # 生成唯一设计ID
        file_ext = model_image.filename.split(".")[-1].lower()
        filename = f"{design_id}.{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)

        # 压缩图片（宽高不超过1024px）
        img = Image.open(BytesIO(content))
        max_size = (1024, 1024)
        img.thumbnail(max_size)
        with open(file_path, "wb") as f:
            img.save(f, format=img.format)

        # 4. 提交异步任务
        task = process_design_task.delay(design_id, description, garment_type)

        # 5. 记录到数据库
        new_task = DesignTask(
            design_id=design_id,
            task_id=task.id,
            description=description,
            garment_type=garment_type,
            image_path=file_path,
            status=DesignStatus.PROCESSING,
            created_at=datetime.utcnow()
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        logger.info(f"设计任务提交成功: design_id={design_id}, task_id={task.id}")
        return JSONResponse({
            "code": 200,
            "message": "设计任务已提交，正在处理中",
            "data": {
                "design_id": design_id,
                "task_id": task.id,
                "preview_url": f"/uploads/{filename}",  # 前端访问图片的URL
                "status": "processing"
            }
        })

    except HTTPException as e:
        logger.warning(f"客户端错误: {e.detail}")
        return JSONResponse({
            "code": e.status_code,
            "message": e.detail,
            "data": None
        })
    except Exception as e:
        logger.error(f"服务器处理失败: {str(e)}", exc_info=True)
        return JSONResponse({
            "code": 500,
            "message": "服务器处理失败，请稍后重试",
            "data": None
        })


@router.get("/task/{task_id}")
async def get_task_status(
        task_id: str,
        db: Session = Depends(get_db)
):
    """查询异步任务状态及结果"""
    try:
        # 查询Celery任务状态
        task = process_design_task.AsyncResult(task_id)

        # 从数据库获取设计任务信息
        design_task = db.query(DesignTask).filter(DesignTask.task_id == task_id).first()
        if not design_task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.ready():
            # 任务完成：更新数据库状态
            if task.successful():
                design_task.status = DesignStatus.COMPLETED
                design_task.spec = task.result  # 保存AI生成的设计规格
                db.commit()
                return JSONResponse({
                    "code": 200,
                    "message": "任务处理完成",
                    "data": {
                        "status": "completed",
                        "design_id": design_task.design_id,
                        "result": task.result  # AI返回的设计详情（颜色、风格等）
                    }
                })
            else:
                # 任务失败
                design_task.status = DesignStatus.FAILED
                db.commit()
                return JSONResponse({
                    "code": 500,
                    "message": "任务处理失败",
                    "data": {"status": "failed", "design_id": design_task.design_id}
                })
        else:
            # 任务处理中
            return JSONResponse({
                "code": 200,
                "message": "任务处理中",
                "data": {
                    "status": "processing",
                    "design_id": design_task.design_id
                }
            })

    except HTTPException as e:
        return JSONResponse({
            "code": e.status_code,
            "message": e.detail,
            "data": None
        })
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}")
        return JSONResponse({
            "code": 500,
            "message": "查询任务状态失败",
            "data": None
        })


@router.get("/designs")
async def get_design_history(
        page: int = 1,
        page_size: int = 10,
        db: Session = Depends(get_db)
):
    """查询设计历史记录（分页）"""
    try:
        if page < 1:
            page = 1
        offset = (page - 1) * page_size

        # 查询分页数据
        query = db.query(DesignTask).order_by(DesignTask.created_at.desc())
        total = query.count()
        tasks = query.offset(offset).limit(page_size).all()

        # 格式化返回数据
        items = []
        for task in tasks:
            # 提取图片文件名（用于前端预览URL）
            img_filename = os.path.basename(task.image_path)
            items.append({
                "design_id": task.design_id,
                "garment_type": task.garment_type,
                "description": task.description,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "preview_url": f"/uploads/{img_filename}",
                "has_result": bool(task.spec)  # 是否有AI生成的结果
            })

        return JSONResponse({
            "code": 200,
            "message": "success",
            "data": {
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        })

    except Exception as e:
        logger.error(f"查询设计历史失败: {str(e)}")
        return JSONResponse({
            "code": 500,
            "message": "查询设计历史失败",
            "data": None
        })