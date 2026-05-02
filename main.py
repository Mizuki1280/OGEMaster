from flask import Flask, render_template, request, redirect, url_for
import os
from data import db_session
from data.users import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ogemasters_secret_key'


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.username == username,
            User.password == password
        ).first()

        if user:
            return redirect(url_for('dashboard', user_id=user.id))
        else:
            return render_template('login.html', error="Неверный логин или пароль")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('register.html', error="Пароли не совпадают")

        db_sess = db_session.create_session()

        if db_sess.query(User).filter(User.username == username).first():
            return render_template('register.html', error="Пользователь с таким именем уже существует")

        if db_sess.query(User).filter(User.email == email).first():
            return render_template('register.html', error="Пользователь с такой почтой уже существует")

        user = User()
        user.username = username
        user.email = email
        user.password = password
        user.total_tasks = 0
        user.completed_tasks = 0

        db_sess.add(user)
        db_sess.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    if not user:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=user)


if __name__ == '__main__':
    os.makedirs("db", exist_ok=True)
    db_session.global_init("db/ogemasters.db")
    app.run(port=8080, host='127.0.0.1', debug=False, threaded=True)