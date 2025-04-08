import sqlite3
from pathlib import Path
import logging
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_stats():
    # Подключаемся к обеим базам данных
    catalog_conn = sqlite3.connect(DB_FILE)
    catalog_cur = catalog_conn.cursor()
    
    telegram_conn = sqlite3.connect('../telegram_bot/published_photos.sqlite')
    telegram_cur = telegram_conn.cursor()
    
    # Получаем статистику из Telegram бота с pHash и путем файла
    telegram_cur.execute("""
        SELECT 
            p.message_id,
            p.views,
            p.forwards,
            GROUP_CONCAT(r.reaction || ':' || r.count) as reactions,
            h.phash,
            s.subscribers_count,
            p.file_path
        FROM published_photos p
        LEFT JOIN reactions r ON p.message_id = r.message_id
        LEFT JOIN photo_hashes h ON p.message_id = h.message_id
        LEFT JOIN subscribers_stats s ON p.message_id = s.message_id
        GROUP BY p.message_id
    """)
    
    stats = {}
    for row in telegram_cur.fetchall():
        message_id, views, forwards, reactions, phash, subscribers, file_path = row
        if phash:
            # Нормализуем просмотры и пересылки относительно количества подписчиков
            normalized_views = (views or 0) / (subscribers or 1)
            normalized_forwards = (forwards or 0) / (subscribers or 1)
            
            stats[phash] = {
                'views': views or 0,
                'forwards': forwards or 0,
                'reactions': reactions or '',
                'subscribers': subscribers or 0,
                'normalized_views': normalized_views,
                'normalized_forwards': normalized_forwards,
                'file_path': file_path
            }
    
    # Получаем все опубликованные фотографии из нашей базы
    catalog_cur.execute(f"""
        SELECT id, phash, path, status 
        FROM {TABLE_NAME} 
        WHERE status = 'published'
    """)
    
    updated = 0
    not_found = 0
    not_found_details = []
    
    for id, phash, path, status in catalog_cur.fetchall():
        found = False
        
        # Пробуем найти по pHash
        if phash and phash in stats:
            stat = stats[phash]
            found = True
        else:
            # Если не нашли по pHash, пробуем найти по пути файла
            path_parts = Path(path).parts
            for phash, stat in stats.items():
                if stat['file_path'] and Path(stat['file_path']).name == Path(path).name:
                    found = True
                    break
        
        if found:
            catalog_cur.execute(f"""
                UPDATE {TABLE_NAME}
                SET views = ?,
                    forwards = ?,
                    reactions = ?,
                    subscribers = ?,
                    normalized_views = ?,
                    normalized_forwards = ?
                WHERE id = ?
            """, (
                stat['views'], 
                stat['forwards'], 
                stat['reactions'], 
                stat['subscribers'],
                stat['normalized_views'],
                stat['normalized_forwards'],
                id
            ))
            updated += 1
        else:
            not_found += 1
            not_found_details.append({
                'id': id,
                'path': path,
                'phash': phash
            })
    
    catalog_conn.commit()
    catalog_conn.close()
    telegram_conn.close()
    
    # Выводим статистику
    logger.info(f"Обновлено {updated} записей")
    logger.info(f"Не найдено статистики для {not_found} фотографий")
    
    if not_found_details:
        logger.info("\nДетали по необработанным фотографиям:")
        for photo in not_found_details:
            logger.info(f"ID: {photo['id']}, Путь: {photo['path']}, pHash: {photo['phash']}")

if __name__ == "__main__":
    import_stats() 