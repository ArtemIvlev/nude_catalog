import sqlite3
import logging
from config import *

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_statuses():
    """Проверяет текущее состояние статусов в базе данных"""
    try:
        # Подключаемся к базе
        logger.info("Подключение к базе данных...")
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        
        # Проверяем общее количество фотографий
        cur.execute("SELECT COUNT(*) FROM photos_ok")
        total_count = cur.fetchone()[0]
        logger.info(f"Всего фотографий в базе: {total_count}")
        
        # Проверяем количество фотографий с нормализованной статистикой
        cur.execute("""
            SELECT COUNT(*) 
            FROM photos_ok 
            WHERE normalized_views IS NOT NULL 
            AND normalized_forwards IS NOT NULL
        """)
        stats_count = cur.fetchone()[0]
        logger.info(f"Фотографий с нормализованной статистикой: {stats_count}")
        
        # Проверяем распределение статусов
        cur.execute("""
            SELECT status, COUNT(*) 
            FROM photos_ok 
            GROUP BY status
        """)
        status_counts = cur.fetchall()
        logger.info("\nРаспределение статусов:")
        for status, count in status_counts:
            logger.info(f"{status or 'NULL'}: {count}")
        
        # Проверяем фотографии со статистикой без статуса
        cur.execute("""
            SELECT COUNT(*) 
            FROM photos_ok 
            WHERE normalized_views IS NOT NULL 
            AND normalized_forwards IS NOT NULL
            AND status IS NULL
        """)
        no_status_count = cur.fetchone()[0]
        logger.info(f"\nФотографий со статистикой без статуса: {no_status_count}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при проверке статусов: {e}")
        raise

if __name__ == "__main__":
    check_statuses() 