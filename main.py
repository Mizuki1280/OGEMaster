import time
import os
from flask import Flask, render_template, request, redirect, url_for, make_response, session, jsonify
from data import db_session
from data.users import User
from data.questions import QuestionGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'itmaster_secret_key'
app.secret_key = 'itmaster_secret_key'

USER_BG_FOLDER = 'static/user_bg'
os.makedirs(USER_BG_FOLDER, exist_ok=True)

question_gen = QuestionGenerator()


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
        user.total_tasks = 0
        user.correct_tasks = 0
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
    total = user.total_tasks or 0
    correct = user.correct_tasks or 0
    if total > 0:
        percent = "{:.2f}".format(correct * 100 / total)
    else:
        percent = "-"
    return render_template('profile.html', user=user, theme=theme, total=total, correct=correct, percent=percent,
                           bg_image=user.background_image)


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
        if user.background_image and os.path.exists(
                user.background_image.replace('/static/user_bg/', USER_BG_FOLDER + '/')):
            old_path = user.background_image.replace('/static/user_bg/', USER_BG_FOLDER + '/')
            if os.path.exists(old_path):
                os.remove(old_path)
        user.background_image = None
    elif bg_type == 'custom':
        file = request.files.get('background_image')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"user_{user_id}.{ext}"
            filepath = os.path.join(USER_BG_FOLDER, filename)
            file.save(filepath)
            user.background_image = f"/static/user_bg/{filename}"
    db_sess.commit()
    return redirect(url_for('profile', user_id=user_id))


@app.route('/rating')
def rating():
    theme = get_theme()
    user_id = request.cookies.get('user_id')
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'total_tasks': user.total_tasks or 0,
            'correct_tasks': user.correct_tasks or 0
        })
    current_user_data = None
    if user_id:
        user = db_sess.get(User, int(user_id))
        if user:
            current_user_data = {
                'id': user.id,
                'username': user.username,
                'total_tasks': user.total_tasks or 0,
                'correct_tasks': user.correct_tasks or 0
            }
    return render_template('rating.html', users=users_data, user=current_user_data, theme=theme)


@app.route('/admin/users')
def admin_users():
    theme = get_theme()
    user_id = request.cookies.get('user_id')
    db_sess = db_session.create_session()
    admin = db_sess.get(User, int(user_id)) if user_id else None
    if not admin or admin.id != 1:
        return redirect(url_for('login'))
    users = db_sess.query(User).all()
    return render_template('admin_users.html', users=users, theme=theme, user=admin)


@app.route('/admin/user/<int:target_id>')
def admin_user_detail(target_id):
    theme = get_theme()
    user_id = request.cookies.get('user_id')
    db_sess = db_session.create_session()
    admin = db_sess.get(User, int(user_id)) if user_id else None
    if not admin or admin.id != 1:
        return redirect(url_for('login'))
    target_user = db_sess.get(User, target_id)
    if not target_user:
        return redirect(url_for('admin_users'))
    return render_template('admin_user_detail.html', user=target_user, theme=theme, admin=admin)


@app.route('/admin/user/<int:target_id>/edit', methods=['POST'])
def admin_edit_user(target_id):
    user_id = request.cookies.get('user_id')
    db_sess = db_session.create_session()
    admin = db_sess.get(User, int(user_id)) if user_id else None
    if not admin or admin.id != 1:
        return redirect(url_for('login'))
    target_user = db_sess.get(User, target_id)
    if not target_user:
        return redirect(url_for('admin_users'))
    target_user.username = request.form.get('username')
    target_user.name = request.form.get('name') or None
    target_user.surname = request.form.get('surname') or None
    target_user.email = request.form.get('email') or None
    target_user.age = request.form.get('age') or None
    target_user.country = request.form.get('country') or None
    target_user.city = request.form.get('city') or None
    target_user.address = request.form.get('address') or None
    target_user.position = request.form.get('position') or None
    target_user.speciality = request.form.get('speciality') or None
    new_password = request.form.get('password')
    if new_password:
        target_user.password = new_password
    total_tasks = request.form.get('total_tasks')
    if total_tasks:
        target_user.total_tasks = int(total_tasks)
    correct_tasks = request.form.get('correct_tasks')
    if correct_tasks:
        target_user.correct_tasks = int(correct_tasks)
    db_sess.commit()
    return redirect(url_for('admin_user_detail', target_id=target_id))


@app.route('/admin/user/<int:target_id>/delete')
def admin_delete_user(target_id):
    user_id = request.cookies.get('user_id')
    db_sess = db_session.create_session()
    admin = db_sess.get(User, int(user_id)) if user_id else None
    if not admin or admin.id != 1:
        return redirect(url_for('login'))
    target_user = db_sess.get(User, target_id)
    if not target_user or target_user.id == 1:
        return redirect(url_for('admin_users'))
    db_sess.delete(target_user)
    db_sess.commit()
    return redirect(url_for('admin_users'))


@app.route('/start_game/<int:user_id>')
def start_game(user_id):
    theme = get_theme()
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return redirect(url_for('login'))
    session['game_stats'] = {'solved': 0, 'skipped': 0, 'unsolved': 0, 'total_questions': 0, 'start_time': time.time()}
    session.pop('current_question', None)
    session['current_question'] = question_gen.generate_question()
    return redirect(url_for('game', user_id=user_id))


@app.route('/game/<int:user_id>')
def game(user_id):
    theme = get_theme()
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return redirect(url_for('login'))
    if 'game_stats' not in session:
        return redirect(url_for('start_game', user_id=user_id))
    if 'current_question' not in session:
        session['current_question'] = question_gen.generate_question()
    question = session['current_question']
    elapsed = int(time.time() - session['game_stats']['start_time'])
    total_questions = session['game_stats']['total_questions']
    return render_template('game.html', user=user, theme=theme, question=question, stats=session['game_stats'],
                           total_questions=total_questions, elapsed=elapsed, bg_image=user.background_image)


@app.route('/check_answer/<int:user_id>', methods=['POST'])
def check_answer(user_id):
    theme = get_theme()
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return redirect(url_for('login'))
    user_answer = request.form.get('answer')
    correct_answer = request.form.get('correct_answer')
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    session['game_stats']['total_questions'] += 1
    total_questions = session['game_stats']['total_questions']
    if is_correct:
        session['game_stats']['solved'] += 1
        user.correct_tasks = (user.correct_tasks or 0) + 1
        message = "Правильно!"
        message_type = "success"
    else:
        session['game_stats']['unsolved'] += 1
        message = f"Неправильно. Ответ: {correct_answer}"
        message_type = "danger"
    user.total_tasks = (user.total_tasks or 0) + 1
    db_sess.commit()
    session.pop('current_question', None)
    session['current_question'] = question_gen.generate_question()
    elapsed = int(time.time() - session['game_stats']['start_time'])
    return render_template('game.html', user=user, theme=theme, question=session['current_question'],
                           stats=session['game_stats'], total_questions=total_questions, elapsed=elapsed,
                           message=message, message_type=message_type, bg_image=user.background_image)


@app.route('/skip_question/<int:user_id>', methods=['POST'])
def skip_question(user_id):
    theme = get_theme()
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return redirect(url_for('login'))
    session['game_stats']['total_questions'] += 1
    total_questions = session['game_stats']['total_questions']
    session['game_stats']['skipped'] += 1
    user.total_tasks = (user.total_tasks or 0) + 1
    db_sess.commit()
    session.pop('current_question', None)
    session['current_question'] = question_gen.generate_question()
    elapsed = int(time.time() - session['game_stats']['start_time'])
    return render_template('game.html', user=user, theme=theme, question=session['current_question'],
                           stats=session['game_stats'], total_questions=total_questions, elapsed=elapsed,
                           message="Задание пропущено", message_type="warning", bg_image=user.background_image)


@app.route('/end_game/<int:user_id>', methods=['POST'])
def end_game(user_id):
    theme = get_theme()
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return redirect(url_for('login'))
    stats = session.pop('game_stats', {'solved': 0, 'skipped': 0, 'unsolved': 0, 'total_questions': 0})
    session.pop('current_question', None)
    total = stats['total_questions']
    elapsed = int(time.time() - stats['start_time'])
    minutes = elapsed // 60
    seconds = elapsed % 60
    return render_template('game_summary.html', user=user, stats=stats, total=total, elapsed=elapsed, minutes=minutes,
                           seconds=seconds, theme=theme)


@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('user_id', '', expires=0)
    return resp


@app.route('/api/users', methods=['GET'])
def api_users():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'total_tasks': u.total_tasks or 0,
        'correct_tasks': u.correct_tasks or 0,
        'percent': round((u.correct_tasks or 0) * 100 / (u.total_tasks or 1), 2) if u.total_tasks else 0
    } for u in users])


@app.route('/api/user/<int:user_id>', methods=['GET'])
def api_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'total_tasks': user.total_tasks or 0,
        'correct_tasks': user.correct_tasks or 0,
        'percent': round((user.correct_tasks or 0) * 100 / (user.total_tasks or 1), 2) if user.total_tasks else 0
    })


@app.route('/api/rating/total', methods=['GET'])
def api_rating_total():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    sorted_users = sorted(users, key=lambda x: x.total_tasks or 0, reverse=True)
    return jsonify([{
        'rank': i + 1,
        'id': u.id,
        'username': u.username,
        'total_tasks': u.total_tasks or 0,
        'correct_tasks': u.correct_tasks or 0,
        'percent': round((u.correct_tasks or 0) * 100 / (u.total_tasks or 1), 2) if u.total_tasks else 0
    } for i, u in enumerate(sorted_users[:10])])


@app.route('/api/rating/correct', methods=['GET'])
def api_rating_correct():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    sorted_users = sorted(users, key=lambda x: x.correct_tasks or 0, reverse=True)
    return jsonify([{
        'rank': i + 1,
        'id': u.id,
        'username': u.username,
        'total_tasks': u.total_tasks or 0,
        'correct_tasks': u.correct_tasks or 0,
        'percent': round((u.correct_tasks or 0) * 100 / (u.total_tasks or 1), 2) if u.total_tasks else 0
    } for i, u in enumerate(sorted_users[:10])])


@app.route('/api/stats/<int:user_id>', methods=['GET'])
def api_stats(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    all_users = db_sess.query(User).all()
    sorted_by_total = sorted(all_users, key=lambda x: x.total_tasks or 0, reverse=True)
    sorted_by_correct = sorted(all_users, key=lambda x: x.correct_tasks or 0, reverse=True)

    rank_total = next((i + 1 for i, u in enumerate(sorted_by_total) if u.id == user_id), None)
    rank_correct = next((i + 1 for i, u in enumerate(sorted_by_correct) if u.id == user_id), None)

    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'total_tasks': user.total_tasks or 0,
            'correct_tasks': user.correct_tasks or 0,
            'percent': round((user.correct_tasks or 0) * 100 / (user.total_tasks or 1), 2) if user.total_tasks else 0
        },
        'rank': {
            'by_total': rank_total,
            'by_correct': rank_correct
        },
        'total_users': len(all_users)
    })


if __name__ == '__main__':
    os.makedirs("db", exist_ok=True)
    db_session.global_init("db/itmaster.db")
    app.run(port=8080, host='127.0.0.1', debug=False, threaded=True)
