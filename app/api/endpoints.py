import os
import uuid
import logging
from datetime import datetime
from io import BytesIO
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.models import DesignTask, DesignStatus
from app.service.tasks import process_design_task
from app.service.ai_services import QianwenService

# 配置日志
logger = logging.getLogger("fashion_ai.endpoints")
logger.setLevel(logging.INFO)

router = APIRouter()

# 允许的文件类型和大小限制（从配置读取）
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]
MAX_FILE_SIZE_MB = settings.MAX_FILE_SIZE // 1024 // 1024

# Mock数据（使用在线图片确保可访问）
MOCK_PRODUCTS = [
    {
        "id": 1,
        "title": "复古撞色卫衣",
        "desc": "灵感来源于 90s 复古街头",
        "palette": "午夜蓝 / 云雾灰",
        "price": 299,
        "tag": "爆款",
        "trend": 82,
        "category": "hot",
        "cover": "https://picsum.photos/300/400?random=1"
    },
    {
        "id": 2,
        "title": "国风刺绣连衣裙",
        "desc": "传统工艺与现代设计的完美结合",
        "palette": "胭脂红 / 墨黑",
        "price": 459,
        "tag": "新品",
        "trend": 75,
        "category": "new",
        "cover": "https://picsum.photos/300/400?random=2"
    },
    {
        "id": 3,
        "title": "机能风工装裤",
        "desc": "都市户外多功能设计",
        "palette": "炭灰 / 军绿",
        "price": 389,
        "tag": "热销",
        "trend": 68,
        "category": "hot",
        "cover": "https://picsum.photos/300/400?random=3"
    }
]

MOCK_VARIANTS = [
    {
        "id": 1,
        "name": "潮流宽松 T 恤",
        "series": "NEO-FLUX",
        "fabric": "云感棉",
        "gradient": "linear-gradient(135deg, #7F7FD5, #86A8E7, #91EAE4)"
    },
    {
        "id": 2,
        "name": "机能风工装裤",
        "series": "URBAN-TECH",
        "fabric": "弹力尼龙",
        "gradient": "linear-gradient(135deg, #2C3E50, #4CA1AF)"
    },
    {
        "id": 3,
        "name": "复古运动夹克",
        "series": "VINTAGE-SPORT",
        "fabric": "复合面料",
        "gradient": "linear-gradient(135deg, #FF512F, #DD2476)"
    }
]

MOCK_INSPIRATIONS = [
    {
        "id": 1,
        "title": "国潮泼墨系列",
        "desc": "以宣纸纹理为灵感",
        "image": "https://picsum.photos/400/300?random=4"
    },
    {
        "id": 2,
        "title": "未来主义金属风",
        "desc": "探索科技与时尚的边界",
        "image": "https://picsum.photos/400/300?random=5"
    },
    {
        "id": 3,
        "title": "自然生态主题",
        "desc": "大地色系与有机材质",
        "image": "https://picsum.photos/400/300?random=6"
    }
]


# ========== 前端需要的核心接口 ==========

@router.get("/products")
async def get_products(
        category: Optional[str] = Query(None, description="产品分类"),
        page: int = Query(1, ge=1, description="页码"),
        pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
        keyword: Optional[str] = Query(None, description="搜索关键词"),
        db: Session = Depends(get_db)
):
    """获取产品列表 - 前端首页核心接口"""
    try:
        # 过滤逻辑
        filtered_products = MOCK_PRODUCTS

        if category and category != "all":
            filtered_products = [p for p in filtered_products if p.get("category") == category]

        if keyword and keyword.strip():
            keyword_lower = keyword.lower().strip()
            filtered_products = [
                p for p in filtered_products
                if keyword_lower in p.get("title", "").lower()
                   or keyword_lower in p.get("desc", "").lower()
            ]

        # 分页逻辑
        start_idx = (page - 1) * pageSize
        end_idx = start_idx + pageSize
        paged_products = filtered_products[start_idx:end_idx]

        return JSONResponse({
            "code": 200,
            "message": "success",
            "data": {
                "products": paged_products,
                "total": len(filtered_products),
                "page": page,
                "pageSize": pageSize
            }
        })

    except Exception as e:
        logger.error(f"获取产品列表失败: {str(e)}")
        return JSONResponse({
            "code": 500,
            "message": "获取产品列表失败",
            "data": None
        })


@router.get("/products/heat-score")
async def get_heat_score(db: Session = Depends(get_db)):
    """获取热度分数 - 前端首页需要"""
    try:
        return JSONResponse({
            "code": 200,
            "message": "success",
            "data": {
                "score": 225  # 模拟热度分数
            }
        })
    except Exception as e:
        logger.error(f"获取热度分数失败: {str(e)}")
        return JSONResponse({
            "code": 500,
            "message": "获取热度分数失败",
            "data": None
        })


@router.get("/preview/variants")
async def get_preview_variants(db: Session = Depends(get_db)):
    """获取3D预览变体列表 - 前端首页需要"""
    try:
        return JSONResponse({
            "code": 200,
            "message": "success",
            "data": MOCK_VARIANTS
        })
    except Exception as e:
        logger.error(f"获取变体列表失败: {str(e)}")
        return JSONResponse({
            "code": 500,
            "message": "获取变体列表失败",
            "data": None
        })


@router.get("/inspirations")
async def get_inspirations(db: Session = Depends(get_db)):
    """获取灵感列表 - 前端首页需要"""
    try:
        return JSONResponse({
            "code": 200,
            "message": "success",
            "data": MOCK_INSPIRATIONS
        })
    except Exception as e:
        logger.error(f"获取灵感列表失败: {str(e)}")
        return JSONResponse({
            "code": 500,
            "message": "获取灵感列表失败",
            "data": None
        })


@router.post("/ai/chat")
async def ai_chat(request_data: dict, db: Session = Depends(get_db)):
    """AI聊天接口 - 前端AI对话功能需要"""
    try:
        message = request_data.get("message", "")
        conversation_id = request_data.get("conversation_id", "")

        # 模拟AI回复（可替换为真实AI服务）
        responses = [
            f"收到您的设计需求：'{message}'。我正在分析您的风格偏好...",
            f"基于'{message}'，我推荐使用中性色调和简约剪裁。",
            f"您的创意'{message}'很有特色！建议搭配天然材质提升舒适度。",
            f"关于'{message}'，考虑加入功能性设计元素提升实用性。"
        ]

        import random
        ai_response = random.choice(responses)

        return JSONResponse({
            "code": 200,
            "message": "success",
            "data": {
                "message": ai_response,
                "conversation_id": conversation_id or f"conv_{uuid.uuid4().hex[:8]}"
            }
        })

    except Exception as e:
        logger.error(f"AI聊天失败: {str(e)}")
        return JSONResponse({
            "code": 500,
            "message": "AI聊天服务暂时不可用",
            "data": None
        })


@router.get("/preview/image/{filename}")
async def get_preview_image(filename: str):
    """获取预览图片 - 解决图片访问问题"""
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            # 返回默认图片或404
            raise HTTPException(status_code=404, detail="图片不存在")

        return FileResponse(file_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图片失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取图片失败")


# ========== 可选接口 ==========

@router.get("/products/search")
async def search_products(
        keyword: str = Query(..., description="搜索关键词"),
        page: int = Query(1, ge=1),
        pageSize: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """搜索产品（可选接口）"""
    try:
        # 复用get_products的逻辑
        return await get_products(
            category=None, page=page, pageSize=pageSize,
            keyword=keyword, db=db
        )
    except Exception as e:
        logger.error(f"搜索产品失败: {str(e)}")
        return JSONResponse({
            "code": 500,
            "message": "搜索失败",
            "data": None
        })


@router.post("/preview/angle")
async def update_preview_angle(request_data: dict):
    """更新预览角度（可选接口）"""
    try:
        angle = request_data.get("angle", 0)
        return JSONResponse({
            "code": 200,
            "message": "角度更新成功",
            "data": {"angle": angle}
        })
    except Exception as e:
        logger.error(f"更新预览角度失败: {str(e)}")
        return JSONResponse({
            "code": 500,
            "message": "更新失败",
            "data": None
        })


@router.post("/preview/report")
async def generate_preview_report(request_data: dict):
    """生成预览报告（可选接口）"""
    try:
        design_id = request_data.get("design_id")
        return JSONResponse({
            "code": 200,
            "message": "报告生成成功",
            "data": {
                "report_id": f"report_{uuid.uuid4().hex[:8]}",
                "design_id": design_id,
                "status": "completed",
                "content": "这是设计分析报告内容..."
            }
        })
    except Exception as e:
        logger.error(f"生成报告失败: {str(e)}")
        return JSONResponse({
            "code": 500,
            "message": "报告生成失败",
            "data": None
        })


# ========== 原有接口保持不变，但优化图片URL返回 ==========

@router.get("/health")
async def health_check():
    """服务健康检查接口，返回基础配置信息"""
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
            },
            "api_endpoints": {
                "products": "/api/v1/products",
                "ai_chat": "/api/v1/ai/chat",
                "design": "/api/v1/ai-design"
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
                {"value": "tshirt", "label": "T恤"},
                {"value": "skirt", "label": "半身裙"},
                {"value": "jacket", "label": "夹克"}
            ],
            "design_status": [
                {"value": "processing", "label": "处理中"},
                {"value": "completed", "label": "已完成"},
                {"value": "failed", "label": "失败"}
            ],
            "product_categories": [
                {"value": "hot", "label": "热门"},
                {"value": "new", "label": "新品"},
                {"value": "sale", "label": "促销"}
            ]
        }
    })


@router.post("/ai-design")
async def create_ai_design(
        description: str = Form(..., description="设计需求描述"),
        garment_type: str = Form(..., description="服装类型"),
        model_image: UploadFile = File(..., description="参考图片"),
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
        design_id = f"design_{uuid.uuid4().hex[:10]}"
        file_ext = model_image.filename.split(".")[-1].lower() if model_image.filename else "jpg"
        filename = f"{design_id}.{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)

        # 压缩图片（宽高不超过1024px）
        img = Image.open(BytesIO(content))
        max_size = (1024, 1024)
        img.thumbnail(max_size)

        # 确保保存为RGB模式
        if img.mode != 'RGB':
            img = img.convert('RGB')

        with open(file_path, "wb") as f:
            img.save(f, format='JPEG', quality=85)

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

        # 返回完整的图片URL
        preview_url = f"/api/v1/preview/image/{filename}"

        return JSONResponse({
            "code": 200,
            "message": "设计任务已提交，正在处理中",
            "data": {
                "design_id": design_id,
                "task_id": task.id,
                "preview_url": preview_url,
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
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """查询异步任务状态及结果"""
    try:
        # 查询Celery任务状态
        task = process_design_task.AsyncResult(task_id)

        # 从数据库获取设计任务信息
        design_task = db.query(DesignTask).filter(DesignTask.task_id == task_id).first()
        if not design_task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.ready():
            if task.successful():
                design_task.status = DesignStatus.COMPLETED
                design_task.spec = task.result
                db.commit()
                return JSONResponse({
                    "code": 200,
                    "message": "任务处理完成",
                    "data": {
                        "status": "completed",
                        "design_id": design_task.design_id,
                        "result": task.result
                    }
                })
            else:
                design_task.status = DesignStatus.FAILED
                db.commit()
                return JSONResponse({
                    "code": 500,
                    "message": "任务处理失败",
                    "data": {"status": "failed", "design_id": design_task.design_id}
                })
        else:
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
            img_filename = os.path.basename(task.image_path)
            items.append({
                "design_id": task.design_id,
                "garment_type": task.garment_type,
                "description": task.description,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "preview_url": f"/api/v1/preview/image/{img_filename}",  # 使用API路径
                "has_result": bool(task.spec)
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