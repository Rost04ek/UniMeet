# Примітки для розробника

## Корисні команди

### Python/Flask

```bash
# Запуск додатку в режимі розробки
python app.py

# Запуск з конкретним портом
python app.py --port 8000

# Перевірка синтаксису
python -m py_compile app.py

# Форматування коду
black app.py models.py config.py
```

### MySQL

```bash
# Підключення до MySQL
mysql -u root -p

# Вибір бази даних
USE student_events_db;

# Експорт бази даних
mysqldump -u root -p student_events_db > backup_$(date +%Y%m%d).sql

# Імпорт бази даних
mysql -u root -p student_events_db < backup.sql

# Перегляд структури таблиці
DESCRIBE users;

# Очистка таблиці
TRUNCATE TABLE registrations;
```

### Git

```bash
# Ініціалізація репозиторію
git init

# Додавання файлів
git add .

# Коміт
git commit -m "Initial commit"

# Створення гілки
git checkout -b feature/new-feature

# Злиття гілок
git merge feature/new-feature
```

## Структура коду

### Додавання нового маршруту

```python
@app.route('/new-route')
@login_required
def new_route():
    models = get_models()
    # Ваша логіка
    return render_template('template.html')
```

### Додавання нової моделі

```python
class NewModel:
    def __init__(self, db):
        self.db = db
    
    def create(self, field1, field2):
        query = "INSERT INTO table_name (field1, field2) VALUES (%s, %s)"
        return self.db.execute_query(query, (field1, field2))
```

### Додавання нового шаблону

```html
{% extends "base.html" %}

{% block title %}Назва сторінки{% endblock %}

{% block content %}
    <!-- Ваш контент -->
{% endblock %}
```

## Налагодження

### Помилки підключення до БД

```python
# В models.py додайте детальне логування
try:
    self.connection = mysql.connector.connect(...)
except mysql.connector.Error as err:
    print(f"Детальна помилка: {err}")
    print(f"Error Code: {err.errno}")
    print(f"SQLSTATE: {err.sqlstate}")
    print(f"Message: {err.msg}")
```

### Логування Flask

```python
import logging

logging.basicConfig(level=logging.DEBUG)
app.logger.debug('Debug message')
app.logger.info('Info message')
app.logger.error('Error message')
```

### Перевірка сесії

```python
from flask import session

@app.route('/debug-session')
def debug_session():
    return {
        'user_id': session.get('user_id'),
        'role': session.get('role')
    }
```

## Оптимізація

### Кешування запитів

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_categories():
    # Запит до БД
    return categories
```

### Пагінація

```python
@app.route('/events')
def events():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    query = f"SELECT * FROM events LIMIT {per_page} OFFSET {offset}"
    events = db.execute_query(query, fetch=True)
    
    return render_template('events.html', events=events, page=page)
```

### Індекси БД

```sql
-- Додайте індекси для часто використовуваних полів
CREATE INDEX idx_events_organizer ON events(organizer_id);
CREATE INDEX idx_registrations_event ON registrations(event_id);
CREATE INDEX idx_events_category ON events(category_id);
```

## Безпека

### Обмеження швидкості запитів

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Логіка входу
    pass
```

### CSRF токени

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# В шаблоні
<form method="POST">
    {{ csrf_token() }}
    <!-- Поля форми -->
</form>
```

### Sanitization вводу

```python
from bleach import clean

def sanitize_input(text):
    return clean(text, tags=[], strip=True)
```

## Розгортання

### Production налаштування

```python
# config.py для production
class ProductionConfig:
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # Інші налаштування
```

### Gunicorn

```bash
pip install gunicorn

# Запуск
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Nginx конфігурація

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/static;
    }
}
```

## Тестування

### Unit тести

```python
import unittest

class TestUserModel(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.user_model = User(self.db)
    
    def test_create_user(self):
        user_id = self.user_model.create(
            'testuser', 'test@example.com', 
            'password', 'Test User'
        )
        self.assertIsNotNone(user_id)
    
    def tearDown(self):
        self.db.disconnect()
```

### Запуск тестів

```bash
python -m unittest discover tests
```

## Моніторинг

### Логування в файл

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
```

### Метрики продуктивності

```python
import time

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        app.logger.info(f'{request.method} {request.path} - {elapsed:.3f}s')
    return response
```

## Backup стратегія

### Автоматичний backup БД

```bash
# Створіть cron job (Linux) або Task Scheduler (Windows)
# Щоденний backup о 2 ночі

0 2 * * * mysqldump -u root -p[PASSWORD] student_events_db > /backups/db_$(date +\%Y\%m\%d).sql
```

### Backup файлів

```bash
# Архівація проекту
tar -czf project_backup_$(date +%Y%m%d).tar.gz /path/to/project
```

## Корисні розширення VS Code

- Python (Microsoft)
- Pylance
- MySQL (Jun Han)
- HTML CSS Support
- JavaScript (ES6) code snippets
- GitLens
- Bracket Pair Colorizer
- Auto Rename Tag

## Ресурси для подальшого навчання

- Flask Mega-Tutorial: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world
- Real Python: https://realpython.com/
- MySQL Tutorial: https://www.mysqltutorial.org/
- MDN Web Docs: https://developer.mozilla.org/

## Контрольний список перед релізом

- [ ] Всі тести пройдені
- [ ] Немає критичних помилок
- [ ] SECRET_KEY змінено на випадковий
- [ ] DEBUG=False у production
- [ ] База даних має backup
- [ ] Логування налаштовано
- [ ] SSL сертифікат встановлено
- [ ] Документація оновлена
- [ ] .env файл не в репозиторії
- [ ] requirements.txt актуальний

## Версіонування

Використовуйте Semantic Versioning (MAJOR.MINOR.PATCH):

- MAJOR - несумісні зміни API
- MINOR - нова функціональність (сумісна)
- PATCH - виправлення помилок

Поточна версія: **1.0.0**
