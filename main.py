from flask import Flask, render_template, request, redirect, url_for, make_response
from data import db_session
from data.users import User
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ogemasters_secret_key'

USER_BG_FOLDER = 'static/user_bg'
os.makedirs(USER_BG_FOLDER, exist_ok=True)


@app.route('/set_theme/<theme>')
def set_theme(theme):
    resp = make_response(redirect(request.referrer or '/'))
    resp.set_cookie('theme', theme, max_age=365 * 24 * 60 * 60)
    return resp


def get_theme():
    return request.cookies.get('theme', 'dark')


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    theme = get_theme()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.username == username).first()

        if user and user.password == password:
            resp = make_response(redirect(url_for('dashboard', user_id=user.id)))
            resp.set_cookie('user_id', str(user.id), max_age=365 * 24 * 60 * 60)
            return resp
        else:
            return render_template('login.html', error="Неверный логин или пароль", theme=theme)

    return render_template('login.html', theme=theme)


@app.route('/register', methods=['GET', 'POST'])
def register():
    theme = get_theme()
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('register.html', error="Пароли не совпадают", theme=theme)

        if not password:
            return render_template('register.html', error="Пароль не может быть пустым", theme=theme)

        db_sess = db_session.create_session()

        if db_sess.query(User).filter(User.username == username).first():
            return render_template('register.html', error="Пользователь с таким именем уже существует", theme=theme)

        if db_sess.query(User).filter(User.email == email).first():
            return render_template('register.html', error="Пользователь с такой почтой уже существует", theme=theme)

        user = User()
        user.username = username
        user.email = email
        user.password = password

        db_sess.add(user)
        db_sess.commit()

        return redirect(url_for('login'))

    return render_template('register.html', theme=theme)


@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    theme = get_theme()
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=user, theme=theme, bg_image=user.background_image)


@app.route('/profile/<int:user_id>')
def profile(user_id):
    theme = get_theme()
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return redirect(url_for('login'))
    return render_template('profile.html', user=user, theme=theme, bg_image=user.background_image)


@app.route('/edit_profile/<int:user_id>', methods=['POST'])
def edit_profile(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return redirect(url_for('login'))

    user.username = request.form.get('username')
    user.name = request.form.get('name')
    user.surname = request.form.get('surname')
    user.email = request.form.get('email')
    user.age = request.form.get('age') or None
    user.country = request.form.get('country')
    user.city = request.form.get('city')
    user.address = request.form.get('address')
    user.position = request.form.get('position')
    user.speciality = request.form.get('speciality')

    db_sess.commit()
    return redirect(url_for('profile', user_id=user_id))


@app.route('/change_password/<int:user_id>', methods=['POST'])
def change_password(user_id):
    theme = get_theme()
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return redirect(url_for('login'))

    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if user.password != old_password:
        return render_template('profile.html', user=user, theme=theme, error="Неверный старый пароль")

    if new_password != confirm_password:
        return render_template('profile.html', user=user, theme=theme, error="Новые пароли не совпадают")

    user.password = new_password
    db_sess.commit()
    return redirect(url_for('profile', user_id=user_id))


@app.route('/set_background/<int:user_id>', methods=['POST'])
def set_background(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return redirect(url_for('login'))

    bg_type = request.form.get('bg_type')

    if bg_type == 'default':
        if user.background_image and os.path.exists(user.background_image):
            os.remove(user.background_image)
        user.background_image = None
    elif bg_type == 'custom':
        file = request.files.get('background_image')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"user_{user_id}.{ext}"
            filepath = os.path.join(USER_BG_FOLDER, filename)
            file.save(filepath)
            filepath_normalized = filepath.replace('\\', '/')
            user.background_image = f"/{filepath_normalized}"

    db_sess.commit()
    return redirect(url_for('profile', user_id=user_id))


@app.route('/rating')
def rating():
    theme = get_theme()
    user_id = request.cookies.get('user_id')
    db_sess = db_session.create_session()
    users = db_sess.query(User).order_by(User.id.desc()).all()
    user = None
    if user_id:
        user = db_sess.get(User, int(user_id))
    return render_template('rating.html', users=users, user=user, theme=theme,
                           bg_image=user.background_image if user else None)


@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('user_id', '', expires=0)
    return resp


if __name__ == '__main__':
    os.makedirs("db", exist_ok=True)
    db_session.global_init("db/ogemasters.db")
    app.run(port=8080, host='127.0.0.1', debug=False, threaded=True)