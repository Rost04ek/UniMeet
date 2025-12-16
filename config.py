import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Конфігурація додатку"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'student_events_db'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    
    DEBUG = os.environ.get('DEBUG') or True
    ITEMS_PER_PAGE = 10
