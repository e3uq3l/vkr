import pgembed
import time
import psycopg2
from psycopg2 import pool
import os
import re


class DatabaseManager:
    def __init__(self, data_dir="./pgdata", db_name="cpkprog_db", min_conn=2, max_conn=10):
        self.data_dir = os.path.abspath(data_dir)
        self.db_name = db_name
        self.pg_server = None
        self.db_uri = None
        self.connection_pool = None
        self.min_conn = min_conn
        self.max_conn = max_conn

    def _wait_for_server(self, timeout=90):
        pid_file = os.path.join(self.data_dir, 'postmaster.pid')
        start_time = time.time()

        while time.time() - start_time < timeout:
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, 'r') as f:
                        lines = f.readlines()
                        status = lines[-1].strip() if lines else ''
                        if status == 'ready':
                            print("Сервер PostgreSQL готов")
                            return True
                        elif status == 'starting':
                            print("Ожидание запуска PostgreSQL...")
                except Exception as e:
                    print(f"Ошибка чтения PID-файла: {e}")
            time.sleep(2)
        raise Exception(f"PostgreSQL не запустился за {timeout} секунд")

    def start(self):
        print("Запуск PostgreSQL...")

        # Убиваем все старые процессы PostgreSQL перед запуском
        import subprocess, sys
        try:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/IM', 'postgres.exe'],
                               capture_output=True, timeout=5,
                               encoding='utf-8', errors='ignore')  # ← ДОБАВИТЬ ЭТО
            else:
                subprocess.run(['pkill', '-9', 'postgres'],
                               capture_output=True, timeout=5)
            time.sleep(2)
            print("Старые процессы PostgreSQL завершены")
        except:
            pass

        try:
            temp_server = pgembed.get_server(self.data_dir)
            temp_server.cleanup()
            print("Очистка выполнена")
            time.sleep(2)
        except Exception as e:
            print(f"Очистка не потребовалась: {e}")

        self.pg_server = pgembed.get_server(self.data_dir)
        self._wait_for_server()

        try:
            base_uri = self.pg_server.get_uri()
        except:
            pid_file = os.path.join(self.data_dir, 'postmaster.pid')
            with open(pid_file, 'r') as f:
                lines = f.readlines()
                port = lines[3].strip() if len(lines) > 3 else '5432'
            base_uri = f"postgresql://postgres:@127.0.0.1:{port}/postgres"

        base_uri_without_db = re.sub(r'/[^/]+$', '', base_uri)
        self.db_uri = f"{base_uri_without_db}/{self.db_name}"

        conn = psycopg2.connect(base_uri)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{self.db_name}'")
            if not cur.fetchone():
                cur.execute(f"CREATE DATABASE {self.db_name}")
                print(f"База данных '{self.db_name}' создана")
        conn.close()

        self.connection_pool = pool.ThreadedConnectionPool(
            self.min_conn,
            self.max_conn,
            self.db_uri
        )
        print(f"Пул соединений создан (мин={self.min_conn}, макс={self.max_conn})")
        print(f"PostgreSQL запущен, URI: {self.db_uri}")

        return self.db_uri

    def stop(self):
        if self.connection_pool:
            self.connection_pool.closeall()
            print("Пул соединений закрыт")
            self.connection_pool = None

        if self.pg_server:
            print("Остановка PostgreSQL...")
            try:
                if hasattr(self.pg_server, 'cleanup'):
                    self.pg_server.cleanup()
                else:
                    print("Метод остановки не найден")
            except Exception as e:
                print(f"Ошибка при остановке: {e}")
            finally:
                self.pg_server = None
                print("PostgreSQL остановлен")

    def get_connection(self):
        """Получает соединение из пула"""
        if not self.connection_pool:
            raise Exception("База данных не запущена. Вызовите start() сначала.")
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """Возвращает соединение в пул"""
        if self.connection_pool:
            self.connection_pool.putconn(conn)