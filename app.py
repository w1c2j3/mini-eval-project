from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, User, EvaluationTask

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'secret_key_for_session'  # 严谨：Flask 闪现消息需要密钥

db.init_app(app)

# 自动创建数据库表（如果数据库里还没表，它会自动帮你建好）
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    # 导师要求：核心流程从登录开始 [cite: 3]
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 1. 获取前端 login.html 中 <input name="username"> 的值
        username = request.form.get('username')
        password = request.form.get('password')

        # 2. 简单的逻辑验证（先跑通为主，直接判断账号密码） [cite: 8]
        # 严谨：实际项目中应查询数据库 db.session.query(User)...
        if username == 'admin' and password == '123456':
            return redirect(url_for('task'))
        else:
            return "登录失败，请检查账号密码"  # 简单提示

    return render_template('login.html')


@app.route('/task')
def task():
    # 评测任务页面
    return render_template('task.html')


if __name__ == '__main__':
    # 开启 debug 模式，修改代码后网页会自动刷新
    app.run(debug=True)

@app.route('/analysis')
def analysis():
    # 从数据库查询所有的评测记录
    tasks = EvaluationTask.query.order_by(EvaluationTask.created_at.desc()).all()
    return render_template('analysis.html', tasks=tasks)