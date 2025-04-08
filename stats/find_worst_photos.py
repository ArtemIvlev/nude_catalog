import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_worst_photos(days_ago=None):
    """Находит фотографии с самыми низкими показателями"""
    try:
        # Подключаемся к базе
        logger.info("Подключение к базе данных...")
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Формируем условие для даты
        date_condition = ""
        if days_ago is not None:
            date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            date_condition = f"AND publication_date < '{date}'"
        
        # Находим фотографии с самыми низкими ненулевыми показателями
        cur.execute(f"""
            SELECT 
                path,
                normalized_views,
                normalized_forwards,
                status,
                publication_date,
                (normalized_views + normalized_forwards) as total_score
            FROM photos_ok 
            WHERE normalized_views IS NOT NULL 
            AND normalized_forwards IS NOT NULL
            AND (normalized_views > 0 OR normalized_forwards > 0)
            {date_condition}
            ORDER BY total_score ASC
            LIMIT 5
        """)
        
        worst_photos = cur.fetchall()
        
        period = "за все время" if days_ago is None else f"за последние {days_ago} дней"
        logger.info(f"\nТоп-5 фотографий с самыми низкими ненулевыми показателями {period}:")
        logger.info("Путь | Просмотры | Пересылки | Статус | Дата публикации | Общий скор")
        logger.info("-" * 100)
        
        for path, views, forwards, status, pub_date, score in worst_photos:
            logger.info(f"{Path(path).name} | {views:.4f} | {forwards:.4f} | {status} | {pub_date or 'Нет'} | {score:.4f}")
        
        # Дополнительно показываем общую статистику
        cur.execute(f"""
            SELECT 
                COUNT(*) as total,
                AVG(normalized_views) as avg_views,
                AVG(normalized_forwards) as avg_forwards,
                AVG(normalized_views + normalized_forwards) as avg_score
            FROM photos_ok 
            WHERE normalized_views IS NOT NULL 
            AND normalized_forwards IS NOT NULL
            AND (normalized_views > 0 OR normalized_forwards > 0)
            {date_condition}
        """)
        
        stats = cur.fetchone()
        logger.info(f"\nОбщая статистика {period} (для ненулевых значений):")
        logger.info(f"Всего фотографий с ненулевой статистикой: {stats[0]}")
        logger.info(f"Средние просмотры: {stats[1]:.4f}")
        logger.info(f"Средние пересылки: {stats[2]:.4f}")
        logger.info(f"Средний общий скор: {stats[3]:.4f}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при поиске фотографий: {e}")
        raise

if __name__ == "__main__":
    # Показываем статистику за последние 7 дней
    find_worst_photos(days_ago=7) 