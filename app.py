from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, User, EvaluationTask

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'secret_key_for_session'

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == '123456':
            return redirect(url_for('task'))
        else:
            return "登录失败，请检查账号密码"

    return render_template('login.html')


@app.route('/task')
def task():
    return render_template('task.html')


if __name__ == '__main__':
    app.run(debug=True)

@app.route('/analysis')
def analysis():
    tasks = EvaluationTask.query.order_by(EvaluationTask.created_at.desc()).all()
    return render_template('analysis.html', tasks=tasks)