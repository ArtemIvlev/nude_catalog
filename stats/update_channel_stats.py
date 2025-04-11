from telethon import TelegramClient
from telethon.tl.functions.stats import GetBroadcastStatsRequest
import sqlite3
import asyncio
from datetime import datetime
import sys
import os
import logging
from pathlib import Path
from config import DB_FILE, TELEGRAM_DB, TABLE_NAME, STATUS_PUBLISHED

# Добавляем путь к конфигурации Telegram бота
sys.path.append('../telegram_bot')
from configs import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_channel_stats():
    # Подключаемся к Telegram используя существующую сессию
    session_path = os.path.join('../telegram_bot', settings.session_name)
    client = TelegramClient(session_path, settings.api_id, settings.api_hash)
    await client.start()
    
    # Получаем информацию о канале
    channel = await client.get_entity(settings.channel_username)
    
    # Подключаемся к базе данных
    conn = sqlite3.connect('../telegram_bot/published_photos.sqlite')
    cur = conn.cursor()
    
    # Создаем таблицу для статистики канала, если её нет
    cur.execute("""
        CREATE TABLE IF NOT EXISTS channel_stats (
            message_id INTEGER PRIMARY KEY,
            subscribers_count INTEGER,
            date TEXT
        )
    """)
    
    try:
        # Получаем текущую статистику канала
        stats = await client(GetBroadcastStatsRequest(
            channel=channel,
            dark=True
        ))
        current_subscribers = stats.followers.current
        print(f"Текущее количество подписчиков: {current_subscribers}")
        
        # Получаем все сообщения
        cur.execute("SELECT message_id, date FROM published_photos ORDER BY date DESC")
        messages = cur.fetchall()
        print(f"Найдено {len(messages)} сообщений")
        
        # Для каждого сообщения сохраняем количество подписчиков
        for message_id, date in messages:
            try:
                cur.execute("""
                    INSERT OR REPLACE INTO channel_stats (message_id, subscribers_count, date)
                    VALUES (?, ?, ?)
                """, (message_id, current_subscribers, date))
                print(f"Обработано сообщение {message_id}: {current_subscribers} подписчиков")
                    
            except Exception as e:
                print(f"Ошибка при обработке сообщения {message_id}: {str(e)}")
    
    except Exception as e:
        print(f"Ошибка при получении статистики канала: {str(e)}")
    
    conn.commit()
    conn.close()
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(get_channel_stats()) 