import sqlite3
import logging
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
from config import *


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_published_delta():
    """Анализирует разницу между количеством фотографий в телеграм-канале и количеством фотографий со статусом 'published' в основной базе данных"""
    try:
        # Подключаемся к базам данных
        logger.info("Подключение к базам данных...")
        main_conn = sqlite3.connect('DB_FILE')
        main_cur = main_conn.cursor()
        
        telegram_conn = sqlite3.connect('../telegram_bot/published_photos.sqlite')
        telegram_cur = telegram_conn.cursor()
        
        # Получаем все фотографии из телеграм канала
        telegram_cur.execute("""
            SELECT p.message_id, p.file_path, h.phash
            FROM published_photos p
            LEFT JOIN photo_hashes h ON p.message_id = h.message_id
            WHERE p.file_path IS NOT NULL
        """)
        
        telegram_photos = telegram_cur.fetchall()
        logger.info(f"Найдено {len(telegram_photos)} фотографий в телеграм канале")
        
        # Получаем все фотографии из основной базы данных со статусом 'published'
        main_cur.execute("""
            SELECT id, path, phash
            FROM photos_ok
            WHERE status = 'published'
        """)
        
        published_photos = main_cur.fetchall()
        logger.info(f"Найдено {len(published_photos)} фотографий со статусом 'published' в основной базе данных")
        
        # Создаем словарь для быстрого поиска по pHash
        phash_dict = defaultdict(list)
        for id, path, phash in published_photos:
            if phash:
                phash_dict[phash].append((id, path))
        
        # Анализируем хеши в телеграм-канале
        telegram_hashes = {}
        for message_id, file_path, phash in telegram_photos:
            if phash:
                if phash not in telegram_hashes:
                    telegram_hashes[phash] = []
                telegram_hashes[phash].append((message_id, file_path))
        
        # Анализируем дубликаты в телеграм-канале
        telegram_duplicates = {phash: photos for phash, photos in telegram_hashes.items() if len(photos) > 1}
        logger.info(f"Найдено {len(telegram_duplicates)} хешей с дубликатами в телеграм-канале")
        
        # Анализируем дубликаты в основной базе данных
        db_duplicates = {phash: photos for phash, photos in phash_dict.items() if len(photos) > 1}
        logger.info(f"Найдено {len(db_duplicates)} хешей с дубликатами в основной базе данных")
        
        # Анализируем хеши, которые есть в телеграм-канале, но нет в основной базе данных
        telegram_only_hashes = set(telegram_hashes.keys()) - set(phash_dict.keys())
        logger.info(f"Найдено {len(telegram_only_hashes)} хешей, которые есть в телеграм-канале, но нет в основной базе данных")
        
        # Анализируем хеши, которые есть в основной базе данных, но нет в телеграм-канале
        db_only_hashes = set(phash_dict.keys()) - set(telegram_hashes.keys())
        logger.info(f"Найдено {len(db_only_hashes)} хешей, которые есть в основной базе данных, но нет в телеграм-канале")
        
        # Анализируем общие хеши
        common_hashes = set(telegram_hashes.keys()) & set(phash_dict.keys())
        logger.info(f"Найдено {len(common_hashes)} общих хешей")
        
        # Анализируем количество фотографий с общими хешами
        total_photos_with_common_hashes = sum(len(phash_dict[phash]) for phash in common_hashes)
        logger.info(f"Всего {total_photos_with_common_hashes} фотографий с общими хешами в основной базе данных")
        
        # Анализируем количество фотографий с уникальными хешами в телеграм-канале
        unique_telegram_hashes = {phash for phash, photos in telegram_hashes.items() if len(photos) == 1}
        logger.info(f"Найдено {len(unique_telegram_hashes)} уникальных хешей в телеграм-канале")
        
        # Анализируем количество фотографий с уникальными хешами в основной базе данных
        unique_db_hashes = {phash for phash, photos in phash_dict.items() if len(photos) == 1}
        logger.info(f"Найдено {len(unique_db_hashes)} уникальных хешей в основной базе данных")
        
        # Анализируем количество фотографий с уникальными хешами, которые есть в телеграм-канале, но нет в основной базе данных
        unique_telegram_only_hashes = unique_telegram_hashes - set(phash_dict.keys())
        logger.info(f"Найдено {len(unique_telegram_only_hashes)} уникальных хешей, которые есть в телеграм-канале, но нет в основной базе данных")
        
        # Анализируем количество фотографий с уникальными хешами, которые есть в основной базе данных, но нет в телеграм-канале
        unique_db_only_hashes = unique_db_hashes - set(telegram_hashes.keys())
        logger.info(f"Найдено {len(unique_db_only_hashes)} уникальных хешей, которые есть в основной базе данных, но нет в телеграм-канале")
        
        # Анализируем количество фотографий с общими уникальными хешами
        common_unique_hashes = unique_telegram_hashes & unique_db_hashes
        logger.info(f"Найдено {len(common_unique_hashes)} общих уникальных хешей")
        
        # Выводим примеры дубликатов в телеграм-канале
        if telegram_duplicates:
            logger.info("\nПримеры дубликатов в телеграм-канале:")
            for phash, photos in list(telegram_duplicates.items())[:5]:
                logger.info(f"Хеш: {phash}")
                for message_id, file_path in photos:
                    logger.info(f"  - {file_path} (message_id: {message_id})")
        
        # Выводим примеры дубликатов в основной базе данных
        if db_duplicates:
            logger.info("\nПримеры дубликатов в основной базе данных:")
            for phash, photos in list(db_duplicates.items())[:5]:
                logger.info(f"Хеш: {phash}")
                for id, path in photos:
                    logger.info(f"  - {path} (id: {id})")
        
        # Выводим примеры хешей, которые есть в телеграм-канале, но нет в основной базе данных
        if telegram_only_hashes:
            logger.info("\nПримеры хешей, которые есть в телеграм-канале, но нет в основной базе данных:")
            for phash in list(telegram_only_hashes)[:5]:
                logger.info(f"Хеш: {phash}")
                for message_id, file_path in telegram_hashes[phash]:
                    logger.info(f"  - {file_path} (message_id: {message_id})")
        
        # Закрываем соединения
        main_conn.close()
        telegram_conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при анализе разницы: {e}")
        raise

if __name__ == "__main__":
    analyze_published_delta() 