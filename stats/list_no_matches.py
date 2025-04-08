import sqlite3
import logging
from pathlib import Path
import imagehash
from PIL import Image
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_no_matches():
    """Получает подробную информацию о фотографиях без совпадений"""
    try:
        # Подключаемся к базам данных
        logger.info("Подключение к базам данных...")
        main_conn = sqlite3.connect('database.db')
        main_cur = main_conn.cursor()
        
        telegram_conn = sqlite3.connect('../telegram_bot/published_photos.sqlite')
        telegram_cur = telegram_conn.cursor()
        
        # Получаем все фотографии из телеграм канала с их phash
        telegram_cur.execute("""
            SELECT p.message_id, p.file_path, h.phash, p.date
            FROM published_photos p
            LEFT JOIN photo_hashes h ON p.message_id = h.message_id
            WHERE p.file_path IS NOT NULL
            ORDER BY p.date DESC
        """)
        
        telegram_photos = telegram_cur.fetchall()
        
        # Получаем все phash из основной базы данных
        main_cur.execute("""
            SELECT phash
            FROM photos_ok
            WHERE phash IS NOT NULL
        """)
        
        main_hashes = {row[0] for row in main_cur.fetchall()}
        
        # Находим фотографии без совпадений
        no_matches = []
        for message_id, file_path, phash, pub_date in telegram_photos:
            if not phash or phash not in main_hashes:
                no_matches.append({
                    'message_id': message_id,
                    'file_path': file_path,
                    'phash': phash,
                    'publication_date': pub_date
                })
        
        # Сохраняем результаты в JSON файл
        with open('no_matches.json', 'w', encoding='utf-8') as f:
            json.dump(no_matches, f, ensure_ascii=False, indent=2)
        
        # Выводим результаты
        logger.info(f"\nНайдено {len(no_matches)} фотографий без совпадений:")
        for photo in no_matches:
            logger.info(f"  - {photo['file_path']}")
            logger.info(f"    Message ID: {photo['message_id']}")
            logger.info(f"    pHash: {photo['phash']}")
            logger.info(f"    Дата публикации: {photo['publication_date']}")
            logger.info("")
        
        logger.info(f"\nРезультаты сохранены в файл no_matches.json")
        
        # Закрываем соединения
        main_conn.close()
        telegram_conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка фотографий: {e}")
        raise

if __name__ == "__main__":
    list_no_matches() 