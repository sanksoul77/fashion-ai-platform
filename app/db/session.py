# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 配置数据库连接（从settings读取配置）
engine = create_engine(
    settings.DATABASE_URL,  # 确保settings.py中定义了数据库URL（如"sqlite:///./fashion.db"）
    connect_args={"check_same_thread": False}  # SQLite专用，其他数据库可删除
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 提供数据库会话（供接口调用）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()