import sqlite3
import os
from tqdm import tqdm
from config import *

def clean_database():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Получаем все записи
    cur.execute(f"SELECT id, path FROM {TABLE_NAME}")
    records = cur.fetchall()
    
    deleted_count = 0
    existing_count = 0
    
    print(f"Проверяем {len(records)} записей...")
    
    # Проверяем каждый файл
    for id, path in tqdm(records, desc="Проверка файлов"):
        if not os.path.exists(path):
            # Удаляем запись о несуществующем файле
            cur.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?", (id,))
            deleted_count += 1
        else:
            existing_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\nСтатистика:")
    print(f"Всего записей: {len(records)}")
    print(f"Существующих файлов: {existing_count}")
    print(f"Удалено записей: {deleted_count}")

if __name__ == "__main__":
    clean_database()
    print("\nГотово!") 