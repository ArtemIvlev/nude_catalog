import sqlite3
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_review_photos():
    """Удаляет все записи с путем review_photos/ из базы данных"""
    try:
        # Подключаемся к базе
        logger.info("Подключение к базе данных...")
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Сначала посчитаем количество записей для удаления
        cur.execute("""
            SELECT COUNT(*)
            FROM photos_ok
            WHERE path LIKE '%review_photos/%'
        """)
        count = cur.fetchone()[0]
        
        if count == 0:
            logger.info("Записей с путем review_photos/ не найдено")
            return
            
        logger.info(f"Найдено {count} записей для удаления")
        
        # Удаляем записи
        cur.execute("""
            DELETE FROM photos_ok
            WHERE path LIKE '%review_photos/%'
        """)
        
        # Сохраняем изменения
        conn.commit()
        
        logger.info(f"Успешно удалено {count} записей")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при удалении записей: {e}")
        raise

if __name__ == "__main__":
    delete_review_photos() 