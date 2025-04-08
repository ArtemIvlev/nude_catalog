import sqlite3
from pathlib import Path
import imagehash
from PIL import Image
from tqdm import tqdm
from config import *

def process_telegram_photos():
    # Подключаемся к базе данных Telegram бота
    telegram_conn = sqlite3.connect('../telegram_bot/published_photos.sqlite')
    telegram_cur = telegram_conn.cursor()
    
    # Создаем таблицу для pHash, если её нет
    telegram_cur.execute("""
        CREATE TABLE IF NOT EXISTS photo_hashes (
            message_id INTEGER PRIMARY KEY,
            phash TEXT
        )
    """)
    
    # Получаем все фотографии
    telegram_cur.execute("""
        SELECT message_id, file_path 
        FROM published_photos 
        WHERE file_path IS NOT NULL
    """)
    
    photos = telegram_cur.fetchall()
    print(f"Найдено {len(photos)} фотографий")
    
    # Обрабатываем каждую фотографию
    for message_id, file_path in tqdm(photos, desc="Обработка фотографий"):
        try:
            # Проверяем, есть ли уже хеш для этого сообщения
            telegram_cur.execute("SELECT phash FROM photo_hashes WHERE message_id = ?", (message_id,))
            if telegram_cur.fetchone():
                continue
            file_path = "../telegram_bot/"+file_path
            # Загружаем изображение и вычисляем pHash
            image = Image.open(file_path)
            phash = str(imagehash.average_hash(image))
            
            # Сохраняем хеш в базу данных
            telegram_cur.execute("""
                INSERT INTO photo_hashes (message_id, phash)
                VALUES (?, ?)
            """, (message_id, phash))
            
        except Exception as e:
            print(f"Ошибка при обработке {file_path}: {str(e)}")
    
    telegram_conn.commit()
    telegram_conn.close()
    print("Готово!")

if __name__ == "__main__":
    process_telegram_photos() 