import sqlite3
import logging
import os
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_review_photos():
    """Проверяет фотографии с путем review_photos/ в базе данных"""
    try:
        # Подключаемся к базе
        logger.info("Подключение к базе данных...")
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Получаем все фотографии с путем review_photos/
        cur.execute("""
            SELECT path, status, publication_date
            FROM photos_ok
            WHERE path LIKE '%review_photos/%'
            ORDER BY path
        """)
        
        review_photos = cur.fetchall()
        
        logger.info(f"\nНайдено {len(review_photos)} фотографий с путем review_photos/:")
        logger.info("Путь | Статус | Дата публикации")
        logger.info("-" * 80)
        
        for path, status, pub_date in review_photos:
            logger.info(f"{path} | {status} | {pub_date or 'Нет'}")
        
        # Проверяем, существуют ли эти файлы
        logger.info("\nПроверка существования файлов:")
        existing_count = 0
        missing_count = 0
        
        for path, _, _ in review_photos:
            if os.path.exists(path):
                existing_count += 1
            else:
                missing_count += 1
                logger.info(f"Файл не найден: {path}")
        
        logger.info(f"\nСуществует файлов: {existing_count}")
        logger.info(f"Отсутствует файлов: {missing_count}")
        
        # Проверяем, есть ли фотографии в директории review_photos, которых нет в базе
        review_dir = "review_photos"
        if os.path.exists(review_dir):
            import glob
            all_files = glob.glob(f"{review_dir}/**/*.*", recursive=True)
            db_paths = {row[0] for row in review_photos}
            
            missing_files = [f for f in all_files if f not in db_paths]
            
            if missing_files:
                logger.info(f"\nНайдено {len(missing_files)} файлов в директории {review_dir}, которых нет в базе:")
                for file in sorted(missing_files):
                    logger.info(f"  - {file}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при проверке фотографий: {e}")
        raise

if __name__ == "__main__":
    check_review_photos() 