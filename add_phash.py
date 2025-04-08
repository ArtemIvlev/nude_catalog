import sqlite3
import imagehash
from PIL import Image
from tqdm import tqdm
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

DB_FILE = "database.db"
TABLE_NAME = "photos_ok"

def compute_phash(image_path):
    try:
        with Image.open(image_path) as img:
            # Преобразуем в RGB, если изображение в другом формате
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Вычисляем average_hash
            return str(imagehash.average_hash(img))
    except Exception as e:
        print(f"Ошибка при вычислении pHash для {image_path}: {e}")
        print(traceback.format_exc())
        return None

def process_batch(batch):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    results = []
    
    for id, path in batch:
        if os.path.exists(path):
            phash = compute_phash(path)
            if phash:
                results.append((id, phash))
    
    # Обновляем записи пакетом
    if results:
        cur.executemany(f"UPDATE {TABLE_NAME} SET phash = ? WHERE id = ?", 
                       [(phash, id) for id, phash in results])
        conn.commit()
    
    conn.close()
    return len(results)

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
    
    # Сбрасываем все pHash значения
    print("Сбрасываем все pHash значения...")
    cur.execute(f"UPDATE {TABLE_NAME} SET phash = NULL")
    conn.commit()
    
    # Получаем все записи без phash
    cur.execute(f"SELECT id, path FROM {TABLE_NAME} WHERE phash IS NULL")
    records = cur.fetchall()
    
    print(f"Найдено {len(records)} записей без pHash")
    
    # Разбиваем записи на пакеты
    batch_size = 100
    batches = [records[i:i + batch_size] for i in range(0, len(records), batch_size)]
    
    # Обрабатываем пакеты в нескольких потоках
    total_processed = 0
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(process_batch, batch) for batch in batches]
        
        for future in tqdm(as_completed(futures), total=len(batches), desc="Обработка пакетов"):
            total_processed += future.result()
    
    print(f"Обработано {total_processed} фотографий")
    conn.close()

if __name__ == "__main__":
    add_phash_column()
    print("Готово!") 