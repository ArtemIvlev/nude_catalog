import sqlite3

DB_FILE = "database.db"
TABLE_NAME = "photos_ok"

def reset_status():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Сбрасываем статус для всех фотографий
    cur.execute(f"UPDATE {TABLE_NAME} SET status = NULL WHERE status = 'done'")
    conn.commit()
    
    # Проверяем количество обновленных записей
    cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE status IS NULL")
    count = cur.fetchone()[0]
    print(f"Сброшено статусов: {count}")
    
    conn.close()

if __name__ == "__main__":
    reset_status()
    print("Готово!") 