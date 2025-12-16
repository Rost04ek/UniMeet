import mysql.connector
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Database:
    """Клас для роботи з базою даних MySQL"""
    
    def __init__(self):
        self.config = Config()
        self.connection = None
    
    def connect(self):
        """Підключення до бази даних"""
        try:
            print(f"\n📡 Спроба підключення до БД...")
            print(f"   Хост: {self.config.MYSQL_HOST}:{self.config.MYSQL_PORT}")
            print(f"   Користувач: {self.config.MYSQL_USER}")
            print(f"   База даних: {self.config.MYSQL_DB}")
            
            self.connection = mysql.connector.connect(
                host=self.config.MYSQL_HOST,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                database=self.config.MYSQL_DB,
                port=self.config.MYSQL_PORT
            )
            print("✅ Успішно підключено до БД!\n")
            return self.connection
        except mysql.connector.Error as err:
            print(f"\n❌ Помилка підключення до БД: {err}")
            print(f"\n⚠️  Перевірте файл .env:")
            print(f"   - MYSQL_HOST має бути адресою сервера БД")
            print(f"   - Переконайтеся, що сервер MySQL запущено")
            print(f"   - Перевірте права доступу користувача\n")
            return None
    
    def disconnect(self):
        """Відключення від бази даних"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def execute_query(self, query, params=None, fetch=False):
        """Виконання SQL запиту"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                self.connection.commit()
                last_id = cursor.lastrowid
                cursor.close()
                return last_id
        except mysql.connector.Error as err:
            print(f"Помилка виконання запиту: {err}")
            self.connection.rollback()
            return None


class User:
    """Модель користувача"""
    
    def __init__(self, db):
        self.db = db
    
    def create(self, email, password, full_name, role='student', university=None):
        """Створення нового користувача"""
        password_hash = generate_password_hash(password)
        query = """
            INSERT INTO users (email, password_hash, full_name, role, university)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.execute_query(query, (email, password_hash, full_name, role, university))
    
    def get_by_id(self, user_id):
        """Отримання користувача за ID"""
        query = "SELECT * FROM users WHERE id = %s"
        result = self.db.execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None
    
    def get_by_email(self, email):
        """Отримання користувача за email"""
        query = "SELECT * FROM users WHERE email = %s"
        result = self.db.execute_query(query, (email,), fetch=True)
        return result[0] if result else None
    
    def verify_password(self, user, password):
        """Перевірка пароля користувача"""
        return check_password_hash(user['password_hash'], password)
    
    def get_all(self):
        """Отримання всіх користувачів"""
        query = "SELECT id, email, full_name, role, university, created_at FROM users ORDER BY created_at DESC"
        return self.db.execute_query(query, fetch=True)
    
    def get_universities(self):
        """Отримання списку університетів"""
        query = "SELECT name as university FROM universities ORDER BY name"
        result = self.db.execute_query(query, fetch=True)
        
        if not result:
            query = "SELECT DISTINCT university FROM users WHERE university IS NOT NULL AND university != '' ORDER BY university"
            result = self.db.execute_query(query, fetch=True)
        
        return result
    
    def update_role(self, user_id, new_role):
        """Оновлення ролі користувача"""
        valid_roles = ['student', 'organizer', 'admin']
        if new_role not in valid_roles:
            return False
        
        query = "UPDATE users SET role = %s WHERE id = %s"
        self.db.execute_query(query, (new_role, user_id))
        return True
    
    def update_user(self, user_id, email=None, full_name=None, university=None, role=None):
        """Оновлення даних користувача"""
        updates = []
        params = []
        
        if email:
            updates.append("email = %s")
            params.append(email)
        
        if full_name:
            updates.append("full_name = %s")
            params.append(full_name)
        
        if university:
            updates.append("university = %s")
            params.append(university)
        
        if role and role in ['student', 'organizer', 'admin']:
            updates.append("role = %s")
            params.append(role)
        
        if not updates:
            return False
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        return self.db.execute_query(query, tuple(params)) is not None


class Event:
    """Модель події"""
    
    def __init__(self, db):
        self.db = db
    
    def create(self, title, description, category_id, organizer_id, location, event_date, 
               registration_deadline, max_participants=100, image_url=None, is_online=False, online_link=None):
        """Створення нової події"""
        query = """
            INSERT INTO events (title, description, category_id, organizer_id, location, 
                               event_date, registration_deadline, max_participants, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute_query(query, (title, description, category_id, organizer_id, 
                                             location, event_date, registration_deadline, 
                                             max_participants, image_url))
    
    def get_by_id(self, event_id):
        """Отримання події за ID"""
        query = """
            SELECT e.*, c.name as category_name, u.full_name as organizer_name, u.email as organizer_email
            FROM events e
            LEFT JOIN event_categories c ON e.category_id = c.id
            LEFT JOIN users u ON e.organizer_id = u.id
            WHERE e.id = %s
        """
        result = self.db.execute_query(query, (event_id,), fetch=True)
        return result[0] if result else None
    
    def get_all(self, status=None, category_id=None, limit=None):
        """Отримання всіх подій з фільтрацією"""
        query = """
            SELECT e.*, c.name as category_name, u.full_name as organizer_name
            FROM events e
            LEFT JOIN event_categories c ON e.category_id = c.id
            LEFT JOIN users u ON e.organizer_id = u.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND e.status = %s"
            params.append(status)
        
        if category_id:
            query += " AND e.category_id = %s"
            params.append(category_id)
        
        query += " ORDER BY e.event_date ASC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        return self.db.execute_query(query, tuple(params) if params else None, fetch=True)
    
    def get_by_organizer(self, organizer_id):
        """Отримання подій організатора"""
        query = """
            SELECT e.*, c.name as category_name
            FROM events e
            LEFT JOIN event_categories c ON e.category_id = c.id
            WHERE e.organizer_id = %s
            ORDER BY e.event_date DESC
        """
        return self.db.execute_query(query, (organizer_id,), fetch=True)
    
    def update(self, event_id, **kwargs):
        """Оновлення події"""
        allowed_fields = ['title', 'description', 'category_id', 'location', 'event_date', 
                         'registration_deadline', 'max_participants', 'status', 'image_url']
        
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = %s")
                params.append(value)
        
        if not updates:
            return False
        
        params.append(event_id)
        query = f"UPDATE events SET {', '.join(updates)} WHERE id = %s"
        return self.db.execute_query(query, tuple(params)) is not None
    
    def delete(self, event_id):
        """Видалення події"""
        query = "DELETE FROM events WHERE id = %s"
        return self.db.execute_query(query, (event_id,)) is not None
    
    def increment_participants(self, event_id):
        """Збільшення кількості учасників"""
        query = "UPDATE events SET current_participants = current_participants + 1 WHERE id = %s"
        return self.db.execute_query(query, (event_id,)) is not None
    
    def decrement_participants(self, event_id):
        """Зменшення кількості учасників"""
        query = "UPDATE events SET current_participants = current_participants - 1 WHERE id = %s AND current_participants > 0"
        return self.db.execute_query(query, (event_id,)) is not None


class Registration:
    """Модель реєстрації"""
    
    def __init__(self, db):
        self.db = db
    
    def create(self, event_id, user_id, notes=None):
        """Створення реєстрації на подію"""
        query = """
            INSERT INTO registrations (event_id, user_id, notes)
            VALUES (%s, %s, %s)
        """
        return self.db.execute_query(query, (event_id, user_id, notes))
    
    def get_by_user(self, user_id):
        """Отримання реєстрацій користувача"""
        query = """
            SELECT r.*, e.title, e.event_date, e.location, e.status as event_status
            FROM registrations r
            JOIN events e ON r.event_id = e.id
            WHERE r.user_id = %s
            ORDER BY r.registration_date DESC
        """
        return self.db.execute_query(query, (user_id,), fetch=True)
    
    def get_by_event(self, event_id):
        """Отримання реєстрацій на подію"""
        query = """
            SELECT r.*, u.full_name, u.email, u.university
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            WHERE r.event_id = %s
            ORDER BY r.registration_date ASC
        """
        return self.db.execute_query(query, (event_id,), fetch=True)
    
    def check_registration(self, event_id, user_id):
        """Перевірка чи зареєстрований користувач"""
        query = "SELECT * FROM registrations WHERE event_id = %s AND user_id = %s"
        result = self.db.execute_query(query, (event_id, user_id), fetch=True)
        return result[0] if result else None
    
    def update_status(self, registration_id, status):
        """Оновлення статусу реєстрації"""
        query = "UPDATE registrations SET status = %s WHERE id = %s"
        return self.db.execute_query(query, (status, registration_id)) is not None
    
    def cancel(self, event_id, user_id):
        """Скасування реєстрації"""
        query = "UPDATE registrations SET status = 'cancelled' WHERE event_id = %s AND user_id = %s"
        return self.db.execute_query(query, (event_id, user_id)) is not None


class Category:
    """Модель категорії"""
    
    def __init__(self, db):
        self.db = db
    
    def get_all(self):
        """Отримання всіх категорій"""
        query = "SELECT * FROM event_categories ORDER BY name ASC"
        return self.db.execute_query(query, fetch=True)
    
    def get_by_id(self, category_id):
        """Отримання категорії за ID"""
        query = "SELECT * FROM event_categories WHERE id = %s"
        result = self.db.execute_query(query, (category_id,), fetch=True)
        return result[0] if result else None


class Comment:
    """Модель коментаря"""
    
    def __init__(self, db):
        self.db = db
    
    def create(self, event_id, user_id, comment_text):
        """Створення коментаря"""
        query = "INSERT INTO comments (event_id, user_id, comment_text) VALUES (%s, %s, %s)"
        return self.db.execute_query(query, (event_id, user_id, comment_text))
    
    def get_by_event(self, event_id):
        """Отримання коментарів події"""
        query = """
            SELECT c.*, u.full_name
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.event_id = %s
            ORDER BY c.created_at DESC
        """
        return self.db.execute_query(query, (event_id,), fetch=True)


class Rating:
    """Модель оцінки"""
    
    def __init__(self, db):
        self.db = db
    
    def create(self, event_id, user_id, rating, review=None):
        """Створення оцінки"""
        query = "INSERT INTO ratings (event_id, user_id, rating, review) VALUES (%s, %s, %s, %s)"
        return self.db.execute_query(query, (event_id, user_id, rating, review))
    
    def get_by_event(self, event_id):
        """Отримання оцінок події"""
        query = """
            SELECT r.*, u.full_name
            FROM ratings r
            JOIN users u ON r.user_id = u.id
            WHERE r.event_id = %s
            ORDER BY r.created_at DESC
        """
        return self.db.execute_query(query, (event_id,), fetch=True)
    
    def get_average(self, event_id):
        """Отримання середньої оцінки події"""
        query = "SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM ratings WHERE event_id = %s"
        result = self.db.execute_query(query, (event_id,), fetch=True)
        return result[0] if result else {'avg_rating': 0, 'count': 0}
