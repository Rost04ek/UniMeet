import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Конфігурація додатку"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Налаштування бази даних
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'student_events_db'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    
    DEBUG = os.environ.get('DEBUG') or True
    ITEMS_PER_PAGE = 10
    
    @classmethod
    def print_config(cls):
        """Виведення поточної конфігурації (без пароля)"""
        print("\n=== Конфігурація підключення до БД ===")
        print(f"Хост: {cls.MYSQL_HOST}:{cls.MYSQL_PORT}")
        print(f"Користувач: {cls.MYSQL_USER}")
        print(f"База даних: {cls.MYSQL_DB}")
        print("====================================\n")

