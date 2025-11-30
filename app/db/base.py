# app/db/base.py
from sqlalchemy.ext.declarative import declarative_base

# 定义基础模型类，所有数据表模型都继承自该类
Base = declarative_base()