import sqlite3
from datetime import datetime, date
import sys
import os

def interpolate_subscribers(post_date, start_date, end_date, start_subs, end_subs):
    """Линейная интерполяция количества подписчиков"""
    total_days = (end_date - start_date).days
    post_days = (post_date - start_date).days
    
    if post_days <= 0:
        return start_subs
    if post_days >= total_days:
        return end_subs
    
    # Линейная интерполяция
    return start_subs + (end_subs - start_subs) * (post_days / total_days)

def update_subscribers():
    # Параметры интерполяции
    start_date = datetime(2023, 11, 5).date()  # 5.11.2023
    end_date = date.today()  # сегодня
    start_subs = 200
    end_subs = 1550
    
    # Подключаемся к базе данных
    conn = sqlite3.connect('../telegram_bot/published_photos.sqlite')
    cur = conn.cursor()
    
    # Создаем таблицу для статистики подписчиков, если её нет
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscribers_stats (
            message_id INTEGER PRIMARY KEY,
            subscribers_count INTEGER,
            date TEXT
        )
    """)
    
    # Получаем все сообщения с датами
    cur.execute("""
        SELECT message_id, date 
        FROM published_photos 
        WHERE date IS NOT NULL
    """)
    messages = cur.fetchall()
    
    print(f"Найдено {len(messages)} сообщений")
    updated = 0
    
    # Обрабатываем каждое сообщение
    for message_id, date_str in messages:
        try:
            # Парсим дату
            post_date = datetime.strptime(date_str.split()[0], '%Y-%m-%d').date()
            
            # Вычисляем количество подписчиков
            subs = int(interpolate_subscribers(
                post_date, start_date, end_date, start_subs, end_subs
            ))
            
            # Сохраняем в базу
            cur.execute("""
                INSERT OR REPLACE INTO subscribers_stats 
                (message_id, subscribers_count, date) 
                VALUES (?, ?, ?)
            """, (message_id, subs, date_str))
            
            updated += 1
            
        except Exception as e:
            print(f"Ошибка при обработке сообщения {message_id}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    print(f"Обновлено {updated} записей")

if __name__ == "__main__":
    update_subscribers() 