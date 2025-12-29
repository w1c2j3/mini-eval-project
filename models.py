from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # 第一阶段先跑通，可存明文 [cite: 8]

class EvaluationTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50))      # 模型名称 (如 Llama3 或 DeepSeek)
    prompt = db.Column(db.Text)                # 测试的问题
    response = db.Column(db.Text)              # 回答内容 [cite: 10]
    latency = db.Column(db.Float)              # 耗时（秒） [cite: 10]
    created_at = db.Column(db.DateTime, server_default=db.func.now())