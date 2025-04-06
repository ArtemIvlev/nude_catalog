import sqlite3
import imagehash
from PIL import Image
from tqdm import tqdm
import os

DB_FILE = "database.db"
TABLE_NAME = "photos_ok"

def compute_phash(image_path):
    try:
        with Image.open(image_path) as img:
            return str(imagehash.average_hash(img))
    except Exception as e:
        print(f"Ошибка при вычислении pHash для {image_path}: {e}")
        return None

def add_phash_column():
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
    
    print(f"Найдено {len(records)} записей без pHash")
    
    # Обновляем записи
    for id, path in tqdm(records, desc="Вычисляем pHash"):
        if os.path.exists(path):
            phash = compute_phash(path)
            if phash:
                cur.execute(f"UPDATE {TABLE_NAME} SET phash = ? WHERE id = ?", (phash, id))
                conn.commit()
    
    conn.close()

if __name__ == "__main__":
    add_phash_column()
    print("Готово!") 