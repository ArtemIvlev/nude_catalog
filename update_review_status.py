import sqlite3
import os
import hashlib
from tqdm import tqdm

DB_FILE = "database.db"
TABLE_NAME = "photos_ok"
REVIEW_DIR = "review_photos"

def compute_sha256(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def update_review_status():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Сбрасываем все статусы в NULL
    print("Сбрасываем все статусы...")
    cur.execute(f"UPDATE {TABLE_NAME} SET status = NULL")
    conn.commit()
    
    # Получаем все файлы в директории ревью и их хеши
    review_files = []
    review_hashes = set()
    
    print("Вычисляем хеши файлов в папке ревью...")
    for filename in tqdm(os.listdir(REVIEW_DIR)):
        filepath = os.path.join(REVIEW_DIR, filename)
        if os.path.isfile(filepath):
            file_hash = compute_sha256(filepath)
            review_files.append((filename, file_hash))
            review_hashes.add(file_hash)
    
    print(f"Найдено {len(review_files)} файлов в директории ревью")
    
    # Обновляем статус для всех файлов с matching хешами
    print("Обновляем статусы в базе данных...")
    placeholders = ','.join(['?' for _ in review_hashes])
    cur.execute(f"""
        UPDATE {TABLE_NAME} 
        SET status = 'approved' 
        WHERE hash_sha256 IN ({placeholders})
    """, list(review_hashes))
    
    approved_count = cur.rowcount
    print(f"Проставлен статус approved для {approved_count} фотографий")
    
    # Проставляем rejected для всех остальных файлов
    cur.execute(f"""
        UPDATE {TABLE_NAME}
        SET status = 'rejected'
        WHERE status IS NULL
    """)
    
    rejected_count = cur.rowcount
    print(f"Проставлен статус rejected для {rejected_count} фотографий")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_review_status()
    print("Готово!") 