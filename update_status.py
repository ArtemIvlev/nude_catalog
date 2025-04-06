import sqlite3
import os
from tqdm import tqdm
from config import *

def update_status():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Получаем список файлов в папке ревью
    review_files = set(os.listdir(REVIEW_DIR))
    
    # Обновляем статус для всех записей
    cur.execute(f"SELECT id, path FROM {TABLE_NAME} WHERE status = ?", (STATUS_REVIEW,))
    records = cur.fetchall()
    
    approved_count = 0
    rejected_count = 0
    
    for id, path in tqdm(records, desc="Обновление статусов"):
        filename = os.path.basename(path)
        if filename in review_files:
            cur.execute(f"UPDATE {TABLE_NAME} SET status = ? WHERE id = ?", (STATUS_APPROVED, id))
            approved_count += 1
        else:
            cur.execute(f"UPDATE {TABLE_NAME} SET status = ? WHERE id = ?", (STATUS_REJECTED, id))
            rejected_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"Одобрено: {approved_count}")
    print(f"Отклонено: {rejected_count}")

if __name__ == "__main__":
    update_status()
    print("Готово!") 