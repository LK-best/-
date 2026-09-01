import os
import re
import urllib.parse
import urllib.request

from flask import Flask, render_template, redirect, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from data import db_session
from data.users import User
from data.car_requests import CarRequest
from forms.user import RegisterForm, LoginForm
from forms.car_request import CarRequestForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "vykupavto_secret_key_2026"
app.config['JSON_AS_ASCII'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

try:
    from telegram_config import TELEGRAM_BOT_TOKEN as _CFG_TOKEN, TELEGRAM_CHAT_ID as _CFG_CHAT
except Exception:
    _CFG_TOKEN = ''
    _CFG_CHAT = ''

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or _CFG_TOKEN or ''
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID') or str(_CFG_CHAT or '')


def parse_int(value):
    if value is None or str(value).strip() == '':
        return None
    digits = re.sub(r'\D', '', str(value))
    return int(digits) if digits else None


def notify_admin(req):
    """Мгновенное оповещение админа в Telegram. Если токен не задан — тихо пропускаем."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print('Telegram пропущен: нет токена или chat id (заполни telegram_config.py)')
        return
    text = (
        f"Новая заявка #{req.id}\n"
        f"Имя: {req.name}\n"
        f"Телефон: {req.phone}\n"
        f"Авто: {req.car_model}\n"
        f"Год: {req.car_year or '—'}\n"
        f"Пробег: {req.mileage or '—'}\n"
        f"Состояние: {req.condition or '—'}\n"
        f"Комментарий: {req.comment or '—'}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
    }).encode()
    try:
        urllib.request.urlopen(url, data=data, timeout=5)
    except Exception as e:
        print('Telegram notify failed:', e)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, int(user_id))


# --- Главная (лендинг) ---

@app.route("/", methods=["GET", "POST"])
@app.route("/submit", methods=["GET", "POST"])
def index():
    form = CarRequestForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        req = CarRequest(
            name=form.name.data,
            phone=form.phone.data,
            car_model=form.car_model.data,
            car_year=parse_int(form.car_year.data),
            mileage=parse_int(form.mileage.data),
            condition=form.condition.data,
            comment=form.comment.data,
            status='Новая'
        )
        if current_user.is_authenticated:
            req.user_id = current_user.id
        db_sess.add(req)
        db_sess.commit()
        notify_admin(req)
        flash('Заявка отправлена! Мы перезвоним вам в ближайшее время.', 'success')
        return redirect("/")

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'error')

    return render_template("index.html", form=form)


# --- Админка заявок ---

@app.route('/admin')
def admin():
    return redirect('/')


@app.route('/admin/delete/<int:req_id>')
@login_required
def delete_request(req_id):
    if current_user.id != 1:
        flash('Доступ запрещён.', 'error')
        return redirect('/')
    db_sess = db_session.create_session()
    req = db_sess.get(CarRequest, req_id)
    if req:
        db_sess.delete(req)
        db_sess.commit()
        flash('Заявка удалена.', 'success')
    else:
        flash('Заявка не найдена.', 'error')
    return redirect('/admin')


# --- Авторизация (из старого проекта) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    return redirect('/')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            flash("Пароли не совпадают", "error")
            return render_template("register.html", title="Регистрация", form=form)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            flash("Такой пользователь уже есть", "error")
            return render_template("register.html", title="Регистрация", form=form)
        user = User(
            name=form.name.data,
            email=form.email.data,
            surname=form.surname.data,
            age=form.age.data,
            position=form.position.data,
            speciality=form.speciality.data,
            address=form.address.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        flash("Регистрация успешна. Войдите в систему.", "success")
        return redirect("/login")
    return render_template("register.html", title="Регистрация", form=form)


# --- Запуск ---

def main():
    db_session.global_init("db/vykupavto.db")
    db_sess = db_session.create_session()

    # Создаём администратора, если его нет
    if not db_sess.query(User).filter(User.id == 1).first():
        admin = User()
        admin.name = "Админ"
        admin.surname = "Админов"
        admin.email = "admin@vykupavto.ru"
        admin.set_password("admin123")
        db_sess.add(admin)
        db_sess.commit()
        print("Создан администратор: admin@vykupavto.ru / admin123")
    app.run(port=8080, host='0.0.0.0', debug=True)
    # Запуск через waitress (production-ready)
    from waitress import serve
    print("Сервер запущен на http://0.0.0.0:5000")
    print("Админка: http://0.0.0.0:5000/admin")
    serve(app, host='0.0.0.0', port=5000)
    



if __name__ == "__main__":
    main()
