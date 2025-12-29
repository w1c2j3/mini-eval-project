import os
from dotenv import load_dotenv

# 加载 .env 文件中的变量
load_dotenv()


class Config:
    # 从环境变量获取数据库信息，如果没有则使用默认值
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'mini_eval_db')

    # 构建 SQLAlchemy 数据库连接字符串
    # 在 localhost 后面加上 :3366
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@localhost:3366/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API 密钥
    REMOTE_API_KEY = os.getenv('REMOTE_API_KEY')
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')