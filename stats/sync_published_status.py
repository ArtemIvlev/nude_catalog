import sqlite3
import logging
from pathlib import Path
from tqdm import tqdm
from config import DB_FILE, TELEGRAM_DB, TABLE_NAME, STATUS_PUBLISHED

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_most_similar(phash, db_photos, min_similarity=0.5):
    """
    Находит максимально похожую фотографию из базы данных
    Возвращает кортеж (id, процент схожести)
    """
    best_match = None
    best_similarity = 0
    
    for photo_id, db_phash in db_photos:
        if not db_phash:
            continue
            
        # Вычисляем разницу между хешами
        diff = sum(c1 != c2 for c1, c2 in zip(phash, db_phash))
        similarity = 1 - (diff / 64.0)  # 64 - максимально возможная разница
        
        if similarity > best_similarity and similarity >= min_similarity:
            best_similarity = similarity
            best_match = photo_id
            
    if best_match:
        return best_match, best_similarity
    return None, 0

def sync_published_status():
    """
    Синхронизирует статус опубликованных фотографий между базой Telegram бота и основной базой
    """
    try:
        # Подключаемся к базам данных
        logger.info("Подключение к базам данных...")
        main_conn = sqlite3.connect(DB_FILE)
        main_cur = main_conn.cursor()
        
        telegram_conn = sqlite3.connect(TELEGRAM_DB)
        telegram_cur = telegram_conn.cursor()
        
        # Получаем список опубликованных фотографий из базы Telegram
        logger.info("Получение списка опубликованных фотографий из базы Telegram...")
        telegram_query = """
            SELECT ph.file_hash, phh.phash 
            FROM published_photos ph
            JOIN photo_hashes phh ON ph.message_id = phh.message_id
            WHERE phh.phash IS NOT NULL
        """
        logger.info(f"Telegram query: {telegram_query}")
        telegram_cur.execute(telegram_query)
        telegram_photos = telegram_cur.fetchall()
        logger.info(f"Найдено {len(telegram_photos)} фотографий в базе Telegram")
        
        # Получаем список фотографий из основной базы
        logger.info("Получение списка фотографий из основной базы...")
        main_query = "SELECT id, phash FROM photos_ok WHERE phash IS NOT NULL"
        logger.info(f"Main query: {main_query}")
        main_cur = main_conn.cursor()
        main_cur.execute(main_query)
        main_photos = main_cur.fetchall()
        logger.info(f"Найдено {len(main_photos)} фотографий в основной базе")
        
        # Создаем словарь для быстрого поиска по pHash
        phash_dict = {}
        for photo_id, phash in main_photos:
            if phash not in phash_dict:
                phash_dict[phash] = []
            phash_dict[phash].append(photo_id)
        
        # Обновляем статус для совпадающих фотографий
        updated_count = 0
        similarity_threshold = 0.80
        
        for file_hash, phash in tqdm(telegram_photos, desc="Обновление статусов"):
            found_match = False
            
            # Сначала проверяем точное совпадение
            if phash in phash_dict:
                for photo_id in phash_dict[phash]:
                    update_query = """
                        UPDATE photos_ok 
                        SET status = 'published'
                        WHERE id = ?
                    """
                    logger.info(f"Update query for exact match: {update_query} with id={photo_id}")
                    main_cur.execute(update_query, (photo_id,))
                    if main_cur.rowcount > 0:
                        updated_count += 1
                found_match = True
            
            if not found_match:
                # Если точного совпадения нет, ищем максимально похожую фотографию
                most_similar_id, similarity = find_most_similar(phash, main_photos, min_similarity=similarity_threshold)
                
                if most_similar_id:
                    update_query = """
                        UPDATE photos_ok 
                        SET status = 'published'
                        WHERE id = ?
                    """
                    logger.info(f"Update query for similar match: {update_query} with id={most_similar_id}, similarity={similarity}")
                    main_cur.execute(update_query, (most_similar_id,))
                    if main_cur.rowcount > 0:
                        updated_count += 1
        
        # Сохраняем изменения
        main_conn.commit()
        
        logger.info(f"Обновлено {updated_count} записей")
        
        # Закрываем соединения
        main_conn.close()
        telegram_conn.close()
        
        logger.info("Синхронизация статусов завершена успешно")
        
    except Exception as e:
        logger.error(f"Ошибка при синхронизации статусов: {e}")
        raise

if __name__ == "__main__":
    sync_published_status() 