import os
import sys
import logging
import psycopg2
from psycopg2.extras import DictCursor

# Добавляем корневую директорию в sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)

from config import TABLE_NAME, PG_CONNECTION_PARAMS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def connect_db():
    """
    Устанавливает соединение с PostgreSQL
    """
    try:
        conn = psycopg2.connect(**PG_CONNECTION_PARAMS)
        return conn
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к PostgreSQL: {str(e)}")
        return None

def ensure_table_schema(conn):
    """
    Создает таблицу если она не существует
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    path TEXT PRIMARY KEY,
                    is_nude BOOLEAN,
                    has_face BOOLEAN,
                    hash_sha256 TEXT,
                    clip_nude_score REAL,
                    nsfw_score REAL,
                    is_small BOOLEAN,
                    status TEXT,
                    phash TEXT,
                    shooting_date TIMESTAMP,
                    modification_date TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("✅ Схема таблицы проверена/создана")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании схемы: {str(e)}")
        conn.rollback()

def insert_or_update_photo(conn, photo_data):
    """
    Вставляет или обновляет информацию о фото
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (
                    path, is_nude, has_face, hash_sha256,
                    clip_nude_score, nsfw_score, is_small,
                    status, phash, shooting_date, modification_date
                ) VALUES (
                    %(path)s, %(is_nude)s, %(has_face)s, %(hash_sha256)s,
                    %(clip_nude_score)s, %(nsfw_score)s, %(is_small)s,
                    %(status)s, %(phash)s, %(shooting_date)s, %(modification_date)s
                )
                ON CONFLICT (path) DO UPDATE SET
                    is_nude = EXCLUDED.is_nude,
                    has_face = EXCLUDED.has_face,
                    hash_sha256 = EXCLUDED.hash_sha256,
                    clip_nude_score = EXCLUDED.clip_nude_score,
                    nsfw_score = EXCLUDED.nsfw_score,
                    is_small = EXCLUDED.is_small,
                    status = EXCLUDED.status,
                    phash = EXCLUDED.phash,
                    shooting_date = EXCLUDED.shooting_date,
                    modification_date = EXCLUDED.modification_date
            """, photo_data)
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка при вставке/обновлении фото: {str(e)}")
        conn.rollback()
        return False

def get_photo_by_path(conn, path):
    """
    Получает информацию о фото по пути
    """
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(f"""
                SELECT * FROM {TABLE_NAME}
                WHERE path = %s
            """, (path,))
            result = cursor.fetchone()
            return dict(result) if result else None
    except Exception as e:
        logger.error(f"❌ Ошибка при получении фото: {str(e)}")
        return None

def get_all_photos(conn):
    """
    Получение всех фото из базы данных
    
    Args:
        conn: объект подключения к базе данных
        
    Returns:
        list: список словарей с данными о фото
    """
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {TABLE_NAME}")
        rows = cursor.fetchall()
        
        if rows:
            # Получаем имена колонок
            columns = [desc[0] for desc in cursor.description]
            # Создаем список словарей с данными
            return [dict(zip(columns, row)) for row in rows]
        return []
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка фото: {str(e)}")
        return [] 