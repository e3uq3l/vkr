from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
import sys
import os
from functools import wraps
from flask import abort

"""
Основной модуль веб-приложения на Flask.
Содержит маршруты для работы со студентами, авторизацию и управление пользователями.
"""

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from BD.validation import validate_student_data, format_validation_errors
from Server.models import User
from Other.logger import app_logger
from BD.crud import insert_student_from_form, update_student_from_form
from BD.queries import get_all_students_with_filters, get_dictionaries, get_student_by_id

app = Flask(__name__)
app.config['SECRET_KEY'] = '123'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'


db_manager = None


COLUMN_NAMES_RU = {
    'id': 'ID',
    'last_name': 'Фамилия',
    'first_name': 'Имя',
    'patronymic': 'Отчество',
    'birth_date': 'Дата рождения',
    'gender': 'Пол',
    'snils': 'СНИЛС',
    'phone': 'Телефон',
    'citizenship_code': 'Гражданство (код)',
    'student_status': 'Статус слушателя',
    'group_code': 'Номер группы',
    'program_type': 'Тип программы',
    'program_name': 'Наименование программы',
    'department': 'Кафедра',
    'learning_form': 'Форма обучения',
    'uses_dot': 'ДОТ',
    'start_date': 'Дата начала',
    'order_enrollment': 'Приказ о зачислении',
    'end_date': 'Дата окончания',
    'order_expulsion': 'Приказ об отчислении',
    'expulsion_reason': 'Причина отчисления',
    'duration_hours': 'Срок (часов)',
    'is_pedagogical': 'Педагогический работник',
    'is_manager': 'Руководитель',
    'funding_source': 'Источник финансирования',
    'customer_type': 'Тип заказчика',
    'customer_name': 'Наименование заказчика',
    'cost': 'Стоимость',
    'document_type': 'Вид документа',
    'document_status': 'Статус документа',
    'document_series': 'Серия документа',
    'document_number': 'Номер документа',
    'document_issue_date': 'Дата выдачи документа',
    'registration_number': 'Регистрационный номер',
    'document_order_issue': 'Приказ о выдаче',
    'professional_field': 'Область деятельности',
    'ugs': 'Укрупнённая группа',
    'economic_activity': 'Вид экономической деятельности',
    'qualification': 'Квалификация',
    'education_level': 'Уровень образования',
    'diploma_lastname': 'Фамилия в дипломе',
    'diploma_series': 'Серия диплома',
    'diploma_number': 'Номер диплома'
}

def set_db_manager(manager):
    global db_manager
    db_manager = manager

@login_manager.user_loader
def load_user(user_id):
    if db_manager:
        return User.get_by_id(db_manager, int(user_id))
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get_by_username(db_manager, username)
        if user and user.check_password(password, user.password_hash):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный логин или пароль', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    if db_manager is None:
        return "База данных не запущена", 500

    try:
        dicts = get_dictionaries(db_manager)

        filters = {
            'search': request.args.get('search', '').strip(),
            'gender': request.args.get('gender', ''),
            'uses_dot': request.args.get('uses_dot', ''),
            'age_min': request.args.get('age_min', ''),
            'age_max': request.args.get('age_max', ''),
            'birth_date_from': request.args.get('birth_date_from', ''),
            'birth_date_to': request.args.get('birth_date_to', ''),
            'start_date_from': request.args.get('start_date_from', ''),
            'start_date_to': request.args.get('start_date_to', ''),
            'is_pedagogical': request.args.get('is_pedagogical', ''),
            'is_manager': request.args.get('is_manager', ''),
            'professional_field': request.args.get('professional_field', '').strip(),
            'qualification': request.args.get('qualification', '').strip(),
            'status_ids': request.args.getlist('status_ids'),
            'department_ids': request.args.getlist('department_ids'),
            'program_ids': request.args.getlist('program_ids'),
            'funding_source_ids': request.args.getlist('funding_source_ids'),
        }

        students, columns = get_all_students_with_filters(db_manager, filters)

        columns_ru = [COLUMN_NAMES_RU.get(col, col) for col in columns]

        return render_template('index.html',
                               students=students,
                               columns=columns,
                               columns_ru=columns_ru,
                               statuses=dicts['statuses'],
                               departments=dicts['departments'],
                               programs=dicts['programs'],
                               funding_sources=dicts['funding_sources'])

    except Exception as e:
        return f"Ошибка при чтении студентов: {e}", 500


@app.route('/add_student', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    if db_manager is None:
        return "База данных не запущена", 500

    if request.method == 'POST':
        is_valid, errors = validate_student_data(request.form)
        if not is_valid:
            error_message = format_validation_errors(errors)
            return render_template('add_student.html', student=None, form_data=request.form, error=error_message), 400
        try:
            insert_student_from_form(request.form, db_manager)
            return redirect(url_for('index'))
        except Exception as e:
            return f"Ошибка при добавлении студента: {e}", 500
    else:
        return render_template('add_student.html', student=None)


@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    if db_manager is None:
        return "База данных не запущена", 500

    if request.method == 'POST':
        is_valid, errors = validate_student_data(request.form)
        if not is_valid:
            error_message = format_validation_errors(errors)
            try:
                student = get_student_by_id(db_manager, student_id)
                if student is None:
                    return "Студент не найден", 404
                return render_template('edit_student.html', student=student, form_data=request.form, error=error_message), 400
            except Exception as e:
                return f"Ошибка при загрузке данных: {e}", 500

        try:
            update_student_from_form(student_id, request.form, db_manager)
            return redirect(url_for('index'))
        except Exception as e:
            return f"Ошибка при обновлении: {e}", 500
    else:
        try:
            student = get_student_by_id(db_manager, student_id)
            if student is None:
                return "Студент не найден", 404
            return render_template('edit_student.html', student=student)
        except Exception as e:
            return f"Ошибка: {e}", 500

@app.route('/delete_student/<int:student_id>')
@login_required
@admin_required
def delete_student(student_id):
    if db_manager is None:
        return "База данных не запущена", 500
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM students WHERE id = %s", (student_id,))
            conn.commit()
        return redirect(url_for('index'))
    except Exception as e:
        return f"Ошибка при удалении: {e}", 500
    finally:
        db_manager.return_connection(conn)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, is_admin FROM users ORDER BY id")
            users = cur.fetchall()
        return render_template('admin/users.html', users=users)
    finally:
        db_manager.return_connection(conn)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_add():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        is_admin = request.form.get('is_admin') == 'on'

        if not username or not password:
            flash('Логин и пароль обязательны', 'danger')
            return render_template('admin/user_form.html', user=None)

        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cur:
                # Проверка на уникальность
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    flash('Пользователь с таким логином уже существует', 'danger')
                    return render_template('admin/user_form.html', user=None)
                # Хешируем пароль
                password_hash = generate_password_hash(password)
                cur.execute(
                    "INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)",
                    (username, password_hash, is_admin)
                )
                conn.commit()
        finally:
            db_manager.return_connection(conn)

        flash('Пользователь добавлен', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/user_form.html', user=None)


@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_edit(user_id):
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        is_admin = request.form.get('is_admin') == 'on'

        if not username:
            flash('Логин обязателен', 'danger')
            return redirect(url_for('admin_user_edit', user_id=user_id))

        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cur:
                # Проверка уникальности логина (исключая текущего)
                cur.execute("SELECT id FROM users WHERE username = %s AND id != %s", (username, user_id))
                if cur.fetchone():
                    flash('Пользователь с таким логином уже существует', 'danger')
                    return redirect(url_for('admin_user_edit', user_id=user_id))

                if password:
                    password_hash = generate_password_hash(password)
                    cur.execute(
                        "UPDATE users SET username=%s, password_hash=%s, is_admin=%s WHERE id=%s",
                        (username, password_hash, is_admin, user_id)
                    )
                else:
                    cur.execute(
                        "UPDATE users SET username=%s, is_admin=%s WHERE id=%s",
                        (username, is_admin, user_id)
                    )
                conn.commit()
        finally:
            db_manager.return_connection(conn)

        flash('Пользователь обновлён', 'success')
        return redirect(url_for('admin_users'))
    else:
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, username, is_admin FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
            if not user:
                abort(404)
            return render_template('admin/user_form.html', user=user)
        finally:
            db_manager.return_connection(conn)


@app.route('/admin/users/delete/<int:user_id>')
@login_required
@admin_required
def admin_user_delete(user_id):
    if user_id == current_user.id:
        flash('Нельзя удалить самого себя', 'danger')
        return redirect(url_for('admin_users'))

    conn = db_manager.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
    finally:
        db_manager.return_connection(conn)

    flash('Пользователь удалён', 'success')
    return redirect(url_for('admin_users'))