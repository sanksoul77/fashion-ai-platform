from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import uuid
import os
import json

router = APIRouter()

@router.get("/test")
def test_api():
    return {"code": 200, "data": "测试接口正常"}

@router.post("/ai-design")
async def create_ai_design(
        description: str,
        model_image: UploadFile = File(...),
        garment_type: Optional[str] = "dress"
):
    """AI设计接口"""
    try:
        # 生成唯一ID
        design_id = str(uuid.uuid4())

        # 验证文件类型
        if not model_image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="请上传图片文件")

        # 保存上传的文件
        file_extension = os.path.splitext(model_image.filename)[1]
        filename = f"{design_id}_model{file_extension}"
        file_path = os.path.join("uploads", filename)

        with open(file_path, "wb") as buffer:
            content = await model_image.read()
            buffer.write(content)

        # 模拟AI处理（后续替换为真实AI）
        design_spec = {
            "design_id": design_id,
            "style": "现代休闲",
            "colors": ["蓝色", "白色"],
            "garment_type": garment_type,
            "status": "processing"
        }

        # 保存设计规格
        spec_path = os.path.join("uploads", f"{design_id}_spec.json")
        with open(spec_path, "w", encoding='utf-8') as f:
            json.dump(design_spec, f, ensure_ascii=False, indent=2)

        return {
            "design_id": design_id,
            "status": "processing",
            "message": f"已收到您的设计需求：{description}",
            "preview_url": f"/uploads/{filename}",
            "spec": design_spec
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败：{str(e)}")


@router.get("/design/{design_id}")
async def get_design_status(design_id: str):
    """获取设计状态"""
    spec_path = os.path.join("uploads", f"{design_id}_spec.json")
    if os.path.exists(spec_path):
        with open(spec_path, "r", encoding='utf-8') as f:
            design_spec = json.load(f)
        return design_spec
    else:
        raise HTTPException(status_code=404, detail="设计任务不存在")

