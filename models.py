from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
class EvaluationTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50))
    prompt = db.Column(db.Text)
    response = db.Column(db.Text)
    latency = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())