import sqlite3
import logging
import os
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_missing_phash():
    """Проверяет файлы, которые были опубликованы в телеграм, но не найдены по phash"""
    try:
        # Подключаемся к базе
        logger.info("Подключение к базе данных...")
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Получаем все опубликованные файлы
        cur.execute("""
            SELECT path, publication_date, phash
            FROM photos_ok
            WHERE publication_date IS NOT NULL
            ORDER BY publication_date DESC
        """)
        
        published_photos = cur.fetchall()
        
        logger.info(f"\nНайдено {len(published_photos)} опубликованных фотографий")
        
        # Проверяем каждый файл
        missing_files = []
        for path, pub_date, phash in published_photos:
            if not os.path.exists(path):
                missing_files.append((path, pub_date))
                logger.info(f"Файл не найден: {path} (опубликован: {pub_date})")
        
        # Выводим статистику
        logger.info(f"\nСтатистика:")
        logger.info(f"Всего опубликованных файлов: {len(published_photos)}")
        logger.info(f"Отсутствующих файлов: {len(missing_files)}")
        
        if missing_files:
            logger.info("\nСписок отсутствующих файлов:")
            for path, pub_date in missing_files:
                logger.info(f"  - {path} (опубликован: {pub_date})")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при проверке файлов: {e}")
        raise

if __name__ == "__main__":
    check_missing_phash() 