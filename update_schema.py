import sqlite3
from config import *

def update_schema():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Добавляем новые колонки, если их нет
    try:
        cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN views INTEGER")
        print("Добавлена колонка views")
    except sqlite3.OperationalError:
        print("Колонка views уже существует")
    
    try:
        cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN forwards INTEGER")
        print("Добавлена колонка forwards")
    except sqlite3.OperationalError:
        print("Колонка forwards уже существует")
    
    try:
        cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN reactions TEXT")
        print("Добавлена колонка reactions")
    except sqlite3.OperationalError:
        print("Колонка reactions уже существует")
    
    try:
        cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN predicted_likes REAL")
        print("Добавлена колонка predicted_likes")
    except sqlite3.OperationalError:
        print("Колонка predicted_likes уже существует")
    
    try:
        cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN subscribers INTEGER")
        print("Добавлена колонка subscribers")
    except sqlite3.OperationalError:
        print("Колонка subscribers уже существует")
    
    try:
        cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN normalized_views REAL")
        print("Добавлена колонка normalized_views")
    except sqlite3.OperationalError:
        print("Колонка normalized_views уже существует")
    
    try:
        cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN normalized_forwards REAL")
        print("Добавлена колонка normalized_forwards")
    except sqlite3.OperationalError:
        print("Колонка normalized_forwards уже существует")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_schema() 