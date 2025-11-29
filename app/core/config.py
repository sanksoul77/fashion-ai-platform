import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "服装定制AI平台"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB


settings = Settings()