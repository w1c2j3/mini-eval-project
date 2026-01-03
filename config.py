import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'mini_eval_db')
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@localhost:3366/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMOTE_API_KEY = os.getenv('REMOTE_API_KEY')
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')