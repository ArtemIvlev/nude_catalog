import sqlite3
from pathlib import Path
import imagehash
from PIL import Image
from tqdm import tqdm
import os
from config import *

def process_telegram_photos():
    # Подключаемся к базе данных Telegram бота
    telegram_conn = sqlite3.connect(TELEGRAM_DB)
    telegram_cur = telegram_conn.cursor()
    
    # Создаем таблицу для pHash, если её нет
    telegram_cur.execute("""
        CREATE TABLE IF NOT EXISTS photo_hashes (
            message_id INTEGER PRIMARY KEY,
            phash TEXT
        )
    """)
    
    # Добавляем колонку file_path, если её нет
    try:
        telegram_cur.execute("""
            ALTER TABLE published_photos 
            ADD COLUMN file_path TEXT
        """)
    except sqlite3.OperationalError:
        pass  # Колонка уже существует
    
    # Получаем все сообщения из published_photos
    telegram_cur.execute("SELECT message_id FROM published_photos")
    message_ids = [row[0] for row in telegram_cur.fetchall()]
    print(f"Найдено {len(message_ids)} сообщений")
    
    # Обрабатываем каждую фотографию
    for message_id in tqdm(message_ids, desc="Обработка фотографий"):
        try:
            # Проверяем, есть ли уже хеш для этого сообщения
            telegram_cur.execute("SELECT phash FROM photo_hashes WHERE message_id = ?", (message_id,))
            if telegram_cur.fetchone():
                continue
                
            # Формируем путь к фотографии
            file_path = f"downloaded/msg_{message_id}.jpg"
            full_path = os.path.join(os.path.dirname(TELEGRAM_DB), file_path)
            
            if not os.path.exists(full_path):
                continue
                
            # Загружаем изображение и вычисляем pHash
            image = Image.open(full_path)
            phash = str(imagehash.average_hash(image))
            
            # Обновляем file_path в базе данных
            telegram_cur.execute("""
                UPDATE published_photos 
                SET file_path = ? 
                WHERE message_id = ?
            """, (file_path, message_id))
            
            # Сохраняем хеш в базу данных
            telegram_cur.execute("""
                INSERT INTO photo_hashes (message_id, phash)
                VALUES (?, ?)
            """, (message_id, phash))
            
        except Exception as e:
            print(f"Ошибка при обработке сообщения {message_id}: {str(e)}")
    
    telegram_conn.commit()
    telegram_conn.close()
    print("Готово!")

if __name__ == "__main__":
    process_telegram_photos() 