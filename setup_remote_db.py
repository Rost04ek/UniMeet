#!/usr/bin/env python3
"""
Утиліта для налаштування та запуску MySQL бази даних на іншому пристрої
Автоматично підключається та створює базу даних для UniMeet
"""

import mysql.connector
from mysql.connector import errorcode
import sys
import os
from dotenv import load_dotenv
from colorama import Fore, Style, init

init(autoreset=True)

# Завантажуємо параметри з .env
load_dotenv()

class RemoteDBSetup:
    def __init__(self):
        self.host = os.getenv('MYSQL_HOST', 'localhost')
        self.user = os.getenv('MYSQL_USER', 'root')
        self.password = os.getenv('MYSQL_PASSWORD', '')
        self.port = int(os.getenv('MYSQL_PORT', 3306))
        self.database = os.getenv('MYSQL_DB', 'student_events_db')
        self.connection = None
        
    def print_header(self):
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.CYAN}🗄️  Налаштування Remote MySQL")
        print(f"{Fore.CYAN}{'='*50}\n")
        
    def print_config(self):
        print(f"{Fore.YELLOW}📋 Поточна конфігурація:")
        print(f"   Хост: {Fore.GREEN}{self.host}:{self.port}")
        print(f"   Користувач: {Fore.GREEN}{self.user}")
        print(f"   База даних: {Fore.GREEN}{self.database}\n")
        
    def test_connection(self):
        """Перевіряємо підключення до MySQL"""
        print(f"{Fore.YELLOW}🔌 Спроба підключення...")
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            print(f"{Fore.GREEN}✅ Успішно підключено до MySQL!\n")
            return True
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print(f"{Fore.RED}❌ Неправильні дані для входу (користувач/пароль)")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print(f"{Fore.RED}❌ База даних не існує")
            else:
                print(f"{Fore.RED}❌ Помилка: {err}")
            return False
        except Exception as err:
            print(f"{Fore.RED}❌ Не вдалось підключитися:")
            print(f"   - Перевір IP адресу хоста: {self.host}")
            print(f"   - Перевір чи MySQL запущено на хості")
            print(f"   - Перевір чи firewall дозволяє порт {self.port}")
            print(f"   Помилка: {err}\n")
            return False
    
    def create_database(self):
        """Створюємо базу даних, якщо її немає"""
        cursor = self.connection.cursor()
        
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            print(f"{Fore.GREEN}✅ База даних '{self.database}' готова\n")
        except mysql.connector.Error as err:
            print(f"{Fore.RED}❌ Помилка при створенні БД: {err}\n")
            return False
        finally:
            cursor.close()
        return True
    
    def create_tables(self):
        """Створюємо таблиці бази даних"""
        cursor = self.connection.cursor()
        
        try:
            cursor.execute(f"USE {self.database}")
            
            # Читаємо SQL схему
            schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
            
            if not os.path.exists(schema_path):
                print(f"{Fore.YELLOW}⚠️  Файл schema.sql не знайдено: {schema_path}")
                print(f"   Таблиці не будуть створені\n")
                return False
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Розділяємо запити по ;
            statements = sql_content.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement)
                    except mysql.connector.Error as err:
                        # Ігноруємо помилки "вже існує"
                        if "already exists" not in str(err).lower():
                            print(f"{Fore.YELLOW}⚠️  {err}")
            
            self.connection.commit()
            print(f"{Fore.GREEN}✅ Таблиці створені успішно\n")
            return True
            
        except Exception as err:
            print(f"{Fore.RED}❌ Помилка при створенні таблиць: {err}\n")
            return False
        finally:
            cursor.close()
    
    def create_remote_user(self):
        """Створюємо користувача для доступу з мережі"""
        cursor = self.connection.cursor()
        
        try:
            # Дозволяємо користувачу доступ з будь-якої машини
            cursor.execute(
                f"GRANT ALL PRIVILEGES ON {self.database}.* TO '{self.user}'@'%' IDENTIFIED BY %s WITH GRANT OPTION",
                (self.password,)
            )
            cursor.execute("FLUSH PRIVILEGES")
            self.connection.commit()
            print(f"{Fore.GREEN}✅ Права доступу оновлені для мережевого доступу\n")
            return True
        except mysql.connector.Error as err:
            print(f"{Fore.YELLOW}⚠️  Не вдалось оновити права: {err}\n")
            return True  # Це не критична помилка
        finally:
            cursor.close()
    
    def test_remote_connection(self):
        """Перевіряємо можливість підключення з мережі"""
        try:
            test_conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            test_cursor = test_conn.cursor()
            test_cursor.execute("SELECT VERSION()")
            version = test_cursor.fetchone()
            print(f"{Fore.GREEN}✅ Мережевий доступ до БД працює!")
            print(f"   MySQL версія: {version[0]}\n")
            test_cursor.close()
            test_conn.close()
            return True
        except Exception as err:
            print(f"{Fore.YELLOW}⚠️  Помилка при тестуванні мережевого доступу: {err}\n")
            return False
    
    def show_connection_info(self):
        """Показуємо інформацію для підключення з інших ПК"""
        print(f"{Fore.CYAN}{'='*50}")
        print(f"{Fore.CYAN}🌐 Інформація для підключення з інших ПК:")
        print(f"{Fore.CYAN}{'='*50}\n")
        
        print(f"{Fore.YELLOW}Скопіюй це в .env файл на іншому ПК:\n")
        print(f"{Fore.GREEN}MYSQL_HOST={self.host}")
        print(f"{Fore.GREEN}MYSQL_PORT={self.port}")
        print(f"{Fore.GREEN}MYSQL_USER={self.user}")
        print(f"{Fore.GREEN}MYSQL_PASSWORD=your_password")
        print(f"{Fore.GREEN}MYSQL_DB={self.database}\n")
    
    def disconnect(self):
        """Закриваємо підключення"""
        if self.connection:
            self.connection.close()
    
    def run(self):
        """Запускаємо весь процес налаштування"""
        self.print_header()
        self.print_config()
        
        if not self.test_connection():
            print(f"{Fore.RED}❌ Не вдалось підключитися до MySQL")
            print(f"{Fore.YELLOW}Дії для вирішення:")
            print(f"   1. Перевір IP адресу: {self.host}")
            print(f"   2. Перевір чи MySQL запущено на цьому хості")
            print(f"   3. Перевір параметри в .env файлі")
            print(f"   4. Перевір чи firewall не блокує порт {self.port}\n")
            return False
        
        if not self.create_database():
            self.disconnect()
            return False
        
        if not self.create_tables():
            self.disconnect()
            return False
        
        if not self.create_remote_user():
            self.disconnect()
            return False
        
        if self.test_remote_connection():
            self.show_connection_info()
        
        self.disconnect()
        
        print(f"{Fore.GREEN}{'='*50}")
        print(f"{Fore.GREEN}✅ Налаштування завершено успішно!")
        print(f"{Fore.GREEN}{'='*50}\n")
        
        return True


def main():
    print(f"{Fore.CYAN}UniMeet - Remote Database Setup\n")
    
    setup = RemoteDBSetup()
    success = setup.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
