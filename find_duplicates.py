import sqlite3
import os
from tqdm import tqdm
import cv2
import numpy as np
from config import *
from PIL import Image
import imagehash

def compute_phash(image_path):
    try:
        # Открываем изображение через PIL для вычисления pHash
        with Image.open(image_path) as img:
            # Вычисляем pHash
            hash = imagehash.average_hash(img)
            return str(hash)
    except Exception as e:
        print(f"Ошибка при обработке {image_path}: {e}")
        return None

def find_duplicates():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Добавляем колонку phash, если её нет
    cur.execute(f"PRAGMA table_info({TABLE_NAME})")
    columns = [row[1] for row in cur.fetchall()]
    if 'phash' not in columns:
        print("Добавляем колонку phash...")
        cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN phash TEXT")
        conn.commit()
    
    # Получаем все записи без phash
    cur.execute(f"SELECT id, path FROM {TABLE_NAME} WHERE phash IS NULL")
    records = cur.fetchall()
    
    print(f"Найдено {len(records)} фотографий без pHash")
    
    # Вычисляем pHash для каждой фотографии
    for id, path in tqdm(records, desc="Вычисление pHash"):
        if os.path.exists(path):
            phash = compute_phash(path)
            if phash:
                cur.execute(f"UPDATE {TABLE_NAME} SET phash = ? WHERE id = ?", (phash, id))
                conn.commit()
    
    # Находим дубликаты
    print("\nПоиск дубликатов...")
    cur.execute(f"""
        WITH Duplicates AS (
            SELECT phash, COUNT(*) as count
            FROM {TABLE_NAME}
            WHERE phash IS NOT NULL
            GROUP BY phash
            HAVING COUNT(*) > 1
        )
        SELECT t.phash, t.id, t.path, t.status, d.count
        FROM {TABLE_NAME} t
        JOIN Duplicates d ON t.phash = d.phash
        ORDER BY t.phash, t.id
    """)
    
    duplicates = cur.fetchall()
    
    if not duplicates:
        print("Дубликатов не найдено!")
        return
    
    # Группируем дубликаты по pHash
    current_hash = None
    group = []
    
    print("\nНайденные дубликаты:")
    for phash, id, path, status, count in duplicates:
        if current_hash != phash:
            if group:
                print(f"\nГруппа из {len(group)} дубликатов (pHash: {current_hash}):")
                for dup in group:
                    print(f"  ID: {dup[0]}, Статус: {dup[2]}, Путь: {dup[1]}")
            current_hash = phash
            group = []
        group.append((id, path, status))
    
    # Выводим последнюю группу
    if group:
        print(f"\nГруппа из {len(group)} дубликатов (pHash: {current_hash}):")
        for dup in group:
            print(f"  ID: {dup[0]}, Статус: {dup[2]}, Путь: {dup[1]}")
    
    conn.close()

if __name__ == "__main__":
    find_duplicates()
    print("\nГотово!") 