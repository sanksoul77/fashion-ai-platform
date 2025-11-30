import os
from dotenv import load_dotenv
from pathlib import Path  # 新增导入

load_dotenv()

class Settings:
    PROJECT_NAME: str = "服装定制AI平台"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # 计算项目根目录
    ROOT_DIR: Path = Path(__file__).parent.parent.parent  # 对应项目根目录
    UPLOAD_DIR: Path = ROOT_DIR / "uploads"  # 绝对路径
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    CELERY_BROKER_URL = "redis://localhost:6379/0"  # Redis地址（确保Redis已启动）
    CELERY_BACKEND_URL = "redis://localhost:6379/0"
    DATABASE_URL = "sqlite:///./fashion.db"  # 数据库URL（根据实际数据库调整）

settings = Settings()