from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from config import Config
from models import Database, User, Event, Registration, Category, Comment, Rating
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)

# Словник перекладу статусів
STATUS_TRANSLATIONS = {
    'upcoming': 'Майбутня',
    'ongoing': 'Поточна',
    'completed': 'Завершена',
    'cancelled': 'Скасована'
}

# Регістрація фільтра для шаблонів
@app.template_filter('translate_status')
def translate_status(status):
    return STATUS_TRANSLATIONS.get(status, status)

# Ініціалізація бази даних
db = Database()

def init_db():
    """Ініціалізація підключення до бази даних"""
    global db
    db.connect()

def get_models():
    """Отримання всіх моделей"""
    return {
        'user': User(db),
        'event': Event(db),
        'registration': Registration(db),
        'category': Category(db),
        'comment': Comment(db),
        'rating': Rating(db)
    }

# Декоратор для перевірки авторизації
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Будь ласка, увійдіть в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Декоратор для перевірки ролі організатора
def organizer_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Будь ласка, увійдіть в систему', 'warning')
            return redirect(url_for('login'))
        
        models = get_models()
        user = models['user'].get_by_id(session['user_id'])
        if user['role'] not in ['organizer', 'admin']:
            flash('У вас немає доступу до цієї сторінки', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Головна сторінка"""
    models = get_models()
    events = models['event'].get_all(status='upcoming', limit=6)
    categories = models['category'].get_all()
    return render_template('index.html', events=events, categories=categories)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Реєстрація нового користувача"""
    models = get_models()
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        university = request.form.get('university')
        
        # Перевірка чи існує користувач
        if models['user'].get_by_email(email):
            flash('Користувач з таким email вже існує', 'danger')
            return redirect(url_for('register'))
        
        # Створення користувача
        user_id = models['user'].create(email, password, full_name, 'student', university)
        
        if user_id:
            flash('Реєстрація успішна! Тепер ви можете увійти', 'success')
            return redirect(url_for('login'))
        else:
            flash('Помилка реєстрації', 'danger')
    
    # Отримання списку університетів для autocomplete
    universities = models['user'].get_universities()
    return render_template('register.html', universities=universities)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вхід користувача"""
    if request.method == 'POST':
        models = get_models()
        
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = models['user'].get_by_email(email)
        
        if user and models['user'].verify_password(user, password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            flash(f'Ласкаво просимо, {user["full_name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Невірний email або пароль', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Вихід користувача"""
    session.clear()
    flash('Ви успішно вийшли з системи', 'info')
    return redirect(url_for('index'))

@app.route('/events')
def events():
    """Список всіх подій"""
    models = get_models()
    
    category_id = request.args.get('category')
    status = request.args.get('status', 'upcoming')
    
    events = models['event'].get_all(status=status, category_id=category_id)
    categories = models['category'].get_all()
    
    return render_template('events.html', events=events, categories=categories, 
                         selected_category=category_id, selected_status=status)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    """Деталі події"""
    models = get_models()
    
    event = models['event'].get_by_id(event_id)
    if not event:
        flash('Подію не знайдено', 'danger')
        return redirect(url_for('events'))
    
    comments = models['comment'].get_by_event(event_id)
    rating_data = models['rating'].get_average(event_id)
    
    is_registered = False
    if 'user_id' in session:
        registration = models['registration'].check_registration(event_id, session['user_id'])
        is_registered = registration is not None and registration['status'] != 'cancelled'
    
    return render_template('event_detail.html', event=event, comments=comments, 
                         rating_data=rating_data, is_registered=is_registered)

@app.route('/event/<int:event_id>/register', methods=['POST'])
@login_required
def register_for_event(event_id):
    """Реєстрація на подію"""
    models = get_models()
    
    event = models['event'].get_by_id(event_id)
    if not event:
        flash('Подію не знайдено', 'danger')
        return redirect(url_for('events'))
    
    # Перевірка чи вже зареєстрований
    existing = models['registration'].check_registration(event_id, session['user_id'])
    if existing and existing['status'] != 'cancelled':
        flash('Ви вже зареєстровані на цю подію', 'warning')
        return redirect(url_for('event_detail', event_id=event_id))
    
    # Перевірка кількості місць
    if event['current_participants'] >= event['max_participants']:
        flash('Вибачте, всі місця зайняті', 'danger')
        return redirect(url_for('event_detail', event_id=event_id))
    
    # Реєстрація (якщо є cancelled запис, відновлюємо його, інакше створюємо новий)
    if existing and existing['status'] == 'cancelled':
        # Відновлення скасованої реєстрації
        success = models['registration'].update_status(existing['id'], 'registered')
    else:
        # Створення нової реєстрації
        reg_id = models['registration'].create(event_id, session['user_id'])
        success = reg_id is not None
    
    if success:
        models['event'].increment_participants(event_id)
        flash('Ви успішно зареєструвалися на подію!', 'success')
    else:
        flash('Помилка реєстрації', 'danger')
    
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/event/<int:event_id>/cancel', methods=['POST'])
@login_required
def cancel_registration(event_id):
    """Скасування реєстрації на подію"""
    models = get_models()
    
    if models['registration'].cancel(event_id, session['user_id']):
        models['event'].decrement_participants(event_id)
        flash('Реєстрацію скасовано', 'info')
    else:
        flash('Помилка скасування реєстрації', 'danger')
    
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/event/<int:event_id>/comment', methods=['POST'])
@login_required
def add_comment(event_id):
    """Додавання коментаря"""
    models = get_models()
    
    comment_text = request.form.get('comment_text')
    if comment_text:
        models['comment'].create(event_id, session['user_id'], comment_text)
        flash('Коментар додано', 'success')
    
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/profile')
@login_required
def profile():
    """Профіль користувача"""
    models = get_models()
    
    user = models['user'].get_by_id(session['user_id'])
    registrations = models['registration'].get_by_user(session['user_id'])
    
    return render_template('profile.html', user=user, registrations=registrations)

@app.route('/create-event', methods=['GET', 'POST'])
@organizer_required
def create_event():
    """Створення нової події"""
    models = get_models()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        location = request.form.get('location')
        event_date = request.form.get('event_date')
        registration_deadline = request.form.get('registration_deadline')
        max_participants = request.form.get('max_participants', 100)
        is_online = request.form.get('is_online') == '1'
        online_link = request.form.get('online_link') if is_online else None
        
        # Валідація обов'язкових полів
        if not title or not description or not category_id or not event_date or not registration_deadline:
            flash('Будь ласка, заповніть всі обов\'язкові поля', 'warning')
            categories = models['category'].get_all()
            return render_template('create_event.html', categories=categories)
        
        # Якщо онлайн, використовуємо "Онлайн" як місце проведення
        if is_online:
            location = 'Онлайн'
        elif not location:
            flash('Вкажіть місце проведення', 'warning')
            categories = models['category'].get_all()
            return render_template('create_event.html', categories=categories)
        
        event_id = models['event'].create(
            title, description, category_id, session['user_id'],
            location, event_date, registration_deadline, max_participants
        )
        
        if event_id:
            flash('Подію успішно створено!', 'success')
            return redirect(url_for('event_detail', event_id=event_id))
        else:
            flash('Помилка створення події', 'danger')
    
    categories = models['category'].get_all()
    return render_template('create_event.html', categories=categories)

@app.route('/my-events')
@organizer_required
def my_events():
    """Мої події (для організаторів)"""
    models = get_models()

    if session.get('role') == 'admin':
        # Адміністратор бачить усі події (майбутні за замовчуванням)
        events = models['event'].get_all()
    else:
        events = models['event'].get_by_organizer(session['user_id'])
    return render_template('my_events.html', events=events)

@app.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
@organizer_required
def edit_event(event_id):
    """Редагування події"""
    models = get_models()
    
    event = models['event'].get_by_id(event_id)
    if not event or (event['organizer_id'] != session['user_id'] and session.get('role') != 'admin'):
        flash('Подію не знайдено або у вас немає прав', 'danger')
        return redirect(url_for('my_events'))
    
    if request.method == 'POST':
        updates = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'category_id': request.form.get('category_id'),
            'location': request.form.get('location'),
            'event_date': request.form.get('event_date'),
            'registration_deadline': request.form.get('registration_deadline'),
            'max_participants': request.form.get('max_participants'),
            'status': request.form.get('status')
        }
        
        if models['event'].update(event_id, **updates):
            flash('Подію оновлено!', 'success')
            return redirect(url_for('event_detail', event_id=event_id))
        else:
            flash('Помилка оновлення події', 'danger')
    
    categories = models['category'].get_all()
    return render_template('edit_event.html', event=event, categories=categories)

@app.route('/event/<int:event_id>/participants')
@organizer_required
def event_participants(event_id):
    """Список учасників події"""
    models = get_models()
    
    event = models['event'].get_by_id(event_id)
    if not event or (event['organizer_id'] != session['user_id'] and session.get('role') != 'admin'):
        flash('Подію не знайдено або у вас немає прав', 'danger')
        return redirect(url_for('events'))
    
    participants = models['registration'].get_by_event(event_id)
    return render_template('participants.html', event=event, participants=participants)


@app.route('/event/<int:event_id>/delete', methods=['POST'])
@organizer_required
def delete_event(event_id):
    """Видалення події організатором або адміном"""
    models = get_models()

    event = models['event'].get_by_id(event_id)
    if not event or (event['organizer_id'] != session['user_id'] and session.get('role') != 'admin'):
        flash('Подію не знайдено або у вас немає прав', 'danger')
        return redirect(url_for('events'))

    if models['event'].delete(event_id):
        flash('Подію видалено', 'success')
    else:
        flash('Не вдалося видалити подію', 'danger')

    if session.get('role') == 'admin':
        return redirect(url_for('events'))
    return redirect(url_for('my_events'))


@app.route('/event/<int:event_id>/participants/add', methods=['POST'])
@organizer_required
def add_participant(event_id):
    """Додавання учасника організатором або адміном"""
    models = get_models()

    event = models['event'].get_by_id(event_id)
    if not event or (event['organizer_id'] != session['user_id'] and session.get('role') != 'admin'):
        flash('Подію не знайдено або у вас немає прав', 'danger')
        return redirect(url_for('events'))

    email = request.form.get('email', '').strip()
    if not email:
        flash('Вкажіть email користувача', 'warning')
        return redirect(url_for('event_participants', event_id=event_id))

    user = models['user'].get_by_email(email)
    if not user:
        flash('Користувача з таким email не знайдено', 'danger')
        return redirect(url_for('event_participants', event_id=event_id))

    existing = models['registration'].check_registration(event_id, user['id'])
    if existing and existing['status'] != 'cancelled':
        flash('Користувач вже доданий до цієї події', 'info')
        return redirect(url_for('event_participants', event_id=event_id))

    if event['current_participants'] >= event['max_participants']:
        flash('Всі місця вже зайняті', 'warning')
        return redirect(url_for('event_participants', event_id=event_id))

    if existing and existing['status'] == 'cancelled':
        success = models['registration'].update_status(existing['id'], 'registered')
    else:
        reg_id = models['registration'].create(event_id, user['id'])
        success = reg_id is not None

    if success:
        models['event'].increment_participants(event_id)
        flash('Учасника додано', 'success')
    else:
        flash('Не вдалося додати учасника', 'danger')

    return redirect(url_for('event_participants', event_id=event_id))


@app.route('/event/<int:event_id>/participants/<int:user_id>/remove', methods=['POST'])
@organizer_required
def remove_participant(event_id, user_id):
    """Видалення учасника організатором або адміном"""
    models = get_models()

    event = models['event'].get_by_id(event_id)
    if not event or (event['organizer_id'] != session['user_id'] and session.get('role') != 'admin'):
        flash('Подію не знайдено або у вас немає прав', 'danger')
        return redirect(url_for('events'))

    registration = models['registration'].check_registration(event_id, user_id)
    if not registration or registration['status'] == 'cancelled':
        flash('Цей учасник вже не активний у події', 'info')
        return redirect(url_for('event_participants', event_id=event_id))

    if models['registration'].cancel(event_id, user_id):
        models['event'].decrement_participants(event_id)
        flash('Учасника видалено', 'success')
    else:
        flash('Не вдалося видалити учасника', 'danger')

    return redirect(url_for('event_participants', event_id=event_id))

@app.route('/users')
def users_list():
    """Список користувачів (тільки для адмінів)"""
    if session.get('user_id') is None:
        flash('Потрібна авторизація', 'danger')
        return redirect(url_for('login'))
    
    models = get_models()
    current_user = models['user'].get_by_id(session.get('user_id'))
    
    if current_user['role'] != 'admin':
        flash('Доступ заборонений', 'danger')
        return redirect(url_for('index'))
    
    all_users = models['user'].get_all()
    return render_template('users.html', users=all_users)

@app.route('/user/<int:user_id>/role', methods=['POST'])
def change_user_role(user_id):
    """Зміна ролі користувача"""
    if session.get('user_id') is None:
        return {'error': 'Unauthorized'}, 401
    
    models = get_models()
    current_user = models['user'].get_by_id(session.get('user_id'))
    
    if current_user['role'] != 'admin':
        return {'error': 'Forbidden'}, 403
    
    new_role = request.form.get('role')
    
    if models['user'].update_role(user_id, new_role):
        flash(f'Роль користувача змінена на {new_role}', 'success')
        return redirect(url_for('users_list'))
    else:
        flash('Невірна роль', 'danger')
        return redirect(url_for('users_list'))

@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Редагування даних користувача"""
    if session.get('user_id') is None:
        flash('Потрібна авторизація', 'danger')
        return redirect(url_for('login'))
    
    models = get_models()
    current_user = models['user'].get_by_id(session.get('user_id'))
    
    if current_user['role'] != 'admin':
        flash('Доступ заборонений', 'danger')
        return redirect(url_for('index'))
    
    user = models['user'].get_by_id(user_id)
    if not user:
        flash('Користувача не знайдено', 'danger')
        return redirect(url_for('users_list'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        university = request.form.get('university')
        role = request.form.get('role')
        
        if models['user'].update_user(user_id, email=email, full_name=full_name, university=university, role=role):
            flash('Дані користувача оновлено', 'success')
            return redirect(url_for('users_list'))
        else:
            flash('Помилка при оновленні даних', 'danger')
    
    return render_template('edit_user.html', user=user)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
