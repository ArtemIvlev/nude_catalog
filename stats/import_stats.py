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
    
    # Получаем все опубликованные фотографии из нашей базы
    catalog_cur.execute(f"""
        SELECT id, message_id 
        FROM {TABLE_NAME} 
        WHERE status = 'published' AND message_id IS NOT NULL
    """)
    
    updated = 0
    not_found = 0
    not_found_details = []
    
    for id, message_id in catalog_cur.fetchall():
        # Получаем статистику из Telegram бота по message_id
        telegram_cur.execute("""
            SELECT 
                p.views,
                p.forwards,
                GROUP_CONCAT(r.reaction || ':' || r.count) as reactions,
                s.subscribers_count
            FROM published_photos p
            LEFT JOIN reactions r ON p.message_id = r.message_id
            LEFT JOIN subscribers_stats s ON p.message_id = s.message_id
            WHERE p.message_id = ?
            GROUP BY p.message_id
        """, (message_id,))
        
        row = telegram_cur.fetchone()
        if row:
            views, forwards, reactions, subscribers = row
            # Нормализуем просмотры и пересылки относительно количества подписчиков
            normalized_views = (views or 0) / (subscribers or 1)
            normalized_forwards = (forwards or 0) / (subscribers or 1)
            
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
                views or 0,
                forwards or 0,
                reactions or '',
                subscribers or 0,
                normalized_views,
                normalized_forwards,
                id
            ))
            updated += 1
        else:
            not_found += 1
            not_found_details.append(f"ID: {id}, Message ID: {message_id}")
    
    # Сохраняем изменения
    catalog_conn.commit()
    
    # Выводим результаты
    logger.info(f"Обновлено записей: {updated}")
    logger.info(f"Не найдено записей: {not_found}")
    
    if not_found_details:
        logger.info("Не найденные записи:")
        for detail in not_found_details[:10]:  # Показываем только первые 10
            logger.info(f"  - {detail}")
        if len(not_found_details) > 10:
            logger.info(f"  ... и еще {len(not_found_details) - 10} записей")
    
    # Закрываем соединения
    catalog_conn.close()
    telegram_conn.close()

if __name__ == "__main__":
    import_stats() 