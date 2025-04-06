import sqlite3
import os
import shutil
from tqdm import tqdm
from config import *

DB_FILE = "database.db"
TABLE_NAME = "photos_ok"
REVIEW_DIR = "review_photos"

def ensure_review_dir():
    if not os.path.exists(REVIEW_DIR):
        os.makedirs(REVIEW_DIR)
        print(f"Создана директория {REVIEW_DIR}")

def prepare_for_review():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Добавляем колонку status, если её нет
    cur.execute(f"PRAGMA table_info({TABLE_NAME})")
    columns = [row[1] for row in cur.fetchall()]
    if 'status' not in columns:
        print("Добавляем колонку status...")
        cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN status TEXT DEFAULT NULL")
        conn.commit()
    
    # Получаем все записи без статуса, только нюды без лиц
    # Используем ROW_NUMBER() для исключения дубликатов по hash_sha256
    cur.execute(f"""
        WITH RankedPhotos AS (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY hash_sha256 ORDER BY id) AS rn
            FROM {TABLE_NAME}
            WHERE status IS NULL
              AND is_nude = 1
              AND has_face = 0
              AND is_small = 0
        )
        SELECT id, path, hash_sha256
        FROM RankedPhotos 
        WHERE rn = 1
    """)
    records = cur.fetchall()
    
    print(f"Найдено {len(records)} уникальных фотографий для ревью (нюды без лиц)")
    
    # Словарь для отслеживания имен файлов и их хешей
    filename_hashes = {}
    
    # Копируем файлы и обновляем статус
    for id, path, hash_sha256 in tqdm(records, desc="Подготовка к ревью"):
        if os.path.exists(path):
            # Получаем базовое имя файла
            filename = os.path.basename(path)
            base_name, ext = os.path.splitext(filename)
            
            # Проверяем, есть ли файл с таким именем но другим хешем
            if filename in filename_hashes:
                if filename_hashes[filename] != hash_sha256:
                    # Если хеш другой, добавляем часть хеша к имени
                    short_hash = hash_sha256[:8]
                    filename = f"{base_name}_{short_hash}{ext}"
            
            review_path = os.path.join(REVIEW_DIR, filename)
            
            # Если файл уже существует в папке ревью, добавляем id
            counter = 1
            while os.path.exists(review_path):
                filename = f"{base_name}_{counter}{ext}"
                review_path = os.path.join(REVIEW_DIR, filename)
                counter += 1
            
            # Копируем файл и сохраняем информацию о нем
            shutil.copy2(path, review_path)
            filename_hashes[filename] = hash_sha256
            
            # Обновляем статус в базе
            cur.execute(f"UPDATE {TABLE_NAME} SET status = ? WHERE id = ?", (STATUS_REVIEW, id))
            conn.commit()
    
    conn.close()

if __name__ == "__main__":
    ensure_review_dir()
    prepare_for_review()
    print("Готово!") 