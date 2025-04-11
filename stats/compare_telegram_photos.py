import sqlite3
import logging
import os
from pathlib import Path
import glob
from config import DB_FILE, TELEGRAM_DB, TABLE_NAME

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compare_telegram_photos():
    """Сравнивает количество фотографий в базе данных и в директории telegram_bot"""
    try:
        # Подключаемся к базе
        logger.info("Подключение к базе данных...")
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        
        # Получаем все фотографии из базы данных
        cur.execute("""
            SELECT path, publication_date
            FROM photos_ok
            WHERE path LIKE '../telegram_bot/%'
            ORDER BY path
        """)
        
        db_photos = cur.fetchall()
        
        # Получаем все фотографии из директории telegram_bot
        telegram_dir = "../telegram_bot"
        if not os.path.exists(telegram_dir):
            logger.error(f"Директория {telegram_dir} не существует")
            return
            
        # Получаем список всех файлов в директории
        all_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            all_files.extend(glob.glob(f"{telegram_dir}/**/{ext}", recursive=True))
        
        # Создаем множества путей для сравнения
        db_paths = {row[0] for row in db_photos}
        fs_paths = set(all_files)
        
        # Находим различия
        only_in_db = db_paths - fs_paths
        only_in_fs = fs_paths - db_paths
        
        # Выводим статистику
        logger.info(f"\nСтатистика:")
        logger.info(f"Всего фотографий в базе данных: {len(db_photos)}")
        logger.info(f"Всего фотографий в директории: {len(all_files)}")
        logger.info(f"Фотографий только в базе данных: {len(only_in_db)}")
        logger.info(f"Фотографий только в директории: {len(only_in_fs)}")
        
        if only_in_db:
            logger.info("\nФотографии, которые есть только в базе данных:")
            for path in sorted(only_in_db):
                logger.info(f"  - {path}")
                
        if only_in_fs:
            logger.info("\nФотографии, которых нет в базе данных:")
            for path in sorted(only_in_fs):
                logger.info(f"  - {path}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при сравнении фотографий: {e}")
        raise

if __name__ == "__main__":
    compare_telegram_photos() 