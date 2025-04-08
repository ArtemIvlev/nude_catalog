import sqlite3
import logging
import os
from pathlib import Path
import glob
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_missing_photos():
    """Добавляет отсутствующие фотографии в базу данных"""
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
        
        # Исключаем системные файлы и логотипы
        missing_photos = {p for p in missing_photos if not any(x in p for x in ['NudeNet/docs', 'NudeNet/in_browser/public'])}
        
        logger.info(f"Найдено {len(missing_photos)} фотографий для добавления в базу")
        
        # Добавляем фотографии в базу
        current_date = datetime.now().strftime('%Y-%m-%d')
        added_count = 0
        
        for photo in missing_photos:
            # Определяем статус на основе директории
            status = 'review'
            if 'review_photos' in photo:
                status = 'review'
            
            # Добавляем фотографию в базу
            cur.execute("""
                INSERT INTO photos_ok (path, status, publication_date)
                VALUES (?, ?, NULL)
            """, (photo, status))
            added_count += 1
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
        logger.info(f"Успешно добавлено {added_count} фотографий в базу данных")
        
    except Exception as e:
        logger.error(f"Ошибка при добавлении фотографий: {e}")
        raise

if __name__ == "__main__":
    add_missing_photos() 