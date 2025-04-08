import sqlite3
import logging
import os
from pathlib import Path
import glob

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_missing_photos():
    """Находит фотографии, которые были опубликованы, но не найдены в базе данных"""
    try:
        # Подключаемся к базе
        logger.info("Подключение к базе данных...")
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Получаем список всех фотографий в базе
        cur.execute("SELECT path FROM photos_ok")
        db_photos = {row[0] for row in cur.fetchall()}
        
        # Получаем список всех фотографий в директории
        logger.info("Поиск всех фотографий в директории...")
        photo_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff', '*.webp']
        all_photos = set()
        
        for ext in photo_extensions:
            photos = glob.glob(f"**/{ext}", recursive=True)
            all_photos.update(photos)
        
        # Находим фотографии, которых нет в базе
        missing_photos = all_photos - db_photos
        
        logger.info(f"\nНайдено {len(missing_photos)} фотографий, которых нет в базе данных:")
        
        # Группируем по директориям для удобства
        missing_by_dir = {}
        for photo in missing_photos:
            dir_path = str(Path(photo).parent)
            if dir_path not in missing_by_dir:
                missing_by_dir[dir_path] = []
            missing_by_dir[dir_path].append(Path(photo).name)
        
        # Выводим результаты
        for dir_path, photos in sorted(missing_by_dir.items()):
            logger.info(f"\nДиректория: {dir_path}")
            for photo in sorted(photos):
                logger.info(f"  - {photo}")
        
        # Проверяем, есть ли фотографии в директории для просмотра
        review_dir = "review"
        if os.path.exists(review_dir):
            review_photos = set(glob.glob(f"{review_dir}/**/*.*", recursive=True))
            review_missing = review_photos - db_photos
            
            if review_missing:
                logger.info(f"\nНайдено {len(review_missing)} фотографий в директории {review_dir}, которых нет в базе:")
                for photo in sorted(review_missing):
                    logger.info(f"  - {Path(photo).name}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при поиске отсутствующих фотографий: {e}")
        raise

if __name__ == "__main__":
    find_missing_photos() 