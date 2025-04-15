import sqlite3
import logging
from tqdm import tqdm
from detect_nude.postgres_db import connect_db, ensure_table_schema
from detect_nude.config import TABLE_NAME, DB_PATH

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def convert_bool(value):
    """
    Преобразует значение в булево
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ('true', '1', 't', 'y', 'yes')
    return False

def convert_float(value):
    """
    Преобразует значение в float
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def migrate_data():
    """
    Мигрирует данные из SQLite в PostgreSQL
    """
    sqlite_conn = None
    pg_conn = None
    
    try:
        # Подключаемся к SQLite
        logger.info("🔄 Подключение к SQLite...")
        sqlite_conn = sqlite3.connect(DB_PATH)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Получаем все записи из SQLite с явным указанием колонок
        sqlite_cursor.execute(f"""
            SELECT 
                path,
                is_nude,
                has_face,
                hash_sha256,
                clip_nude_score,
                nsfw_score,
                is_small,
                status,
                phash,
                shooting_date,
                modification_date
            FROM {TABLE_NAME}
        """)
        rows = sqlite_cursor.fetchall()
        
        # Подключаемся к PostgreSQL
        logger.info("🔄 Подключение к PostgreSQL...")
        pg_conn = connect_db()
        if not pg_conn:
            logger.error("❌ Не удалось подключиться к PostgreSQL")
            return
            
        # Создаем схему таблицы
        ensure_table_schema(pg_conn)
        
        # Мигрируем данные
        success_count = 0
        error_count = 0
        
        logger.info(f"🔄 Начинаем миграцию {len(rows)} записей...")
        
        # Создаем новый курсор для каждой записи
        for row in tqdm(rows, desc="Миграция"):
            try:
                # Создаем словарь с данными
                photo_data = {
                    'path': str(row[0]) if row[0] is not None else None,
                    'is_nude': convert_bool(row[1]),
                    'has_face': convert_bool(row[2]),
                    'hash_sha256': str(row[3]) if row[3] is not None else None,
                    'clip_nude_score': convert_float(row[4]),
                    'nsfw_score': convert_float(row[5]),
                    'is_small': convert_bool(row[6]),
                    'status': str(row[7]) if row[7] is not None else None,
                    'phash': str(row[8]) if row[8] is not None else None,
                    'shooting_date': row[9],
                    'modification_date': row[10]
                }
                
                with pg_conn.cursor() as pg_cursor:
                    # Вставляем данные
                    pg_cursor.execute(f"""
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
                    pg_conn.commit()  # Фиксируем изменения после каждой записи
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при миграции записи: {str(e)}")
                logger.error(f"Данные записи: {photo_data}")
                error_count += 1
                pg_conn.rollback()  # Откатываем изменения при ошибке
                    
        logger.info(f"✅ Миграция завершена. Успешно: {success_count}, Ошибок: {error_count}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при миграции: {str(e)}")
    finally:
        # Закрываем соединения
        if sqlite_conn:
            sqlite_conn.close()
        if pg_conn:
            pg_conn.close()

if __name__ == "__main__":
    migrate_data() 