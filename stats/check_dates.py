import sqlite3
import logging
from datetime import datetime
from config import DB_FILE

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_publication_dates():
    """Проверяет распределение дат публикации"""
    try:
        # Подключаемся к базе
        logger.info("Подключение к базе данных...")
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        
        # Проверяем распределение дат публикации
        cur.execute("""
            SELECT 
                publication_date,
                COUNT(*) as count,
                AVG(normalized_views) as avg_views,
                AVG(normalized_forwards) as avg_forwards
            FROM photos_ok 
            WHERE publication_date IS NOT NULL
            GROUP BY publication_date
            ORDER BY publication_date DESC
        """)
        
        date_stats = cur.fetchall()
        
        logger.info("\nСтатистика по датам публикации:")
        logger.info("Дата | Количество фото | Средние просмотры | Средние пересылки")
        logger.info("-" * 80)
        
        for date, count, views, forwards in date_stats:
            logger.info(f"{date} | {count:5d} | {views or 0:.4f} | {forwards or 0:.4f}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при проверке дат: {e}")
        raise

if __name__ == "__main__":
    check_publication_dates() 