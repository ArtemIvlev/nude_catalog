import sqlite3
import logging
from pathlib import Path
from config import DB_FILE, TELEGRAM_DB, TABLE_NAME, STATUS_PUBLISHED
from tqdm import tqdm

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_message_ids():
    """Обновляет message_id в таблице photos_ok на основе данных из published_photos.sqlite"""
    try:
        # Подключаемся к базам данных
        logger.info("Подключение к базам данных...")
        main_conn = sqlite3.connect('database.db')
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
        
        # Получаем все фотографии из основной базы данных
        main_cur.execute("""
            SELECT path, phash
            FROM photos_ok
            WHERE phash IS NOT NULL
        """)
        
        main_photos = main_cur.fetchall()
        logger.info(f"Найдено {len(main_photos)} фотографий в основной базе данных")
        
        # Создаем словарь для быстрого поиска по pHash
        phash_dict = {}
        for path, phash in main_photos:
            if phash not in phash_dict:
                phash_dict[phash] = []
            phash_dict[phash].append(path)
        
        # Обновляем message_id
        updated_count = 0
        
        for message_id, file_path, phash in tqdm(telegram_photos, desc="Обновление message_id"):
            if not phash:
                continue
                
            if phash in phash_dict:
                # Обновляем message_id для всех фотографий с этим хешем
                for photo_path in phash_dict[phash]:
                    main_cur.execute("""
                        UPDATE photos_ok 
                        SET message_id = ?, status = 'published'
                        WHERE path = ?
                    """, (message_id, photo_path))
                    if main_cur.rowcount > 0:
                        updated_count += 1
        
        # Сохраняем изменения в базе данных
        main_conn.commit()
        
        # Выводим результаты
        logger.info(f"\nРезультаты обновления:")
        logger.info(f"Всего фотографий в телеграм канале: {len(telegram_photos)}")
        logger.info(f"Обновлено записей: {updated_count}")
        
        # Закрываем соединения
        main_conn.close()
        telegram_conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении message_id: {e}")
        raise

if __name__ == "__main__":
    update_message_ids() 