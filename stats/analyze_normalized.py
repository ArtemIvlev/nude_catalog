import sqlite3
from config import *

def analyze_normalized():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Общая статистика
    cur.execute(f"""
        SELECT 
            COUNT(*) as total,
            AVG(views) as avg_views,
            AVG(normalized_views) as avg_norm_views,
            AVG(forwards) as avg_forwards,
            AVG(normalized_forwards) as avg_norm_forwards,
            AVG(subscribers) as avg_subscribers
        FROM {TABLE_NAME}
        WHERE views IS NOT NULL
    """)
    stats = cur.fetchone()
    
    print("=== Общая статистика ===")
    print(f"Всего фотографий со статистикой: {stats[0]}")
    print(f"Среднее количество просмотров: {stats[1]:.1f}")
    print(f"Среднее нормализованное количество просмотров: {stats[2]:.3f}")
    print(f"Среднее количество пересылок: {stats[3]:.1f}")
    print(f"Среднее нормализованное количество пересылок: {stats[4]:.3f}")
    print(f"Среднее количество подписчиков: {stats[5]:.1f}")
    
    # Топ-10 по нормализованным просмотрам
    print("\n=== Топ-10 по нормализованным просмотрам ===")
    cur.execute(f"""
        SELECT path, views, normalized_views, subscribers, forwards, reactions
        FROM {TABLE_NAME}
        WHERE normalized_views IS NOT NULL
        ORDER BY normalized_views DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"\nФото: {row[0]}")
        print(f"Просмотры: {row[1]} ({row[2]:.3f} на подписчика)")
        print(f"Подписчиков: {row[3]}")
        print(f"Пересылки: {row[4]}")
        print(f"Реакции: {row[5]}")
    
    # Топ-10 по нормализованным пересылкам
    print("\n=== Топ-10 по нормализованным пересылкам ===")
    cur.execute(f"""
        SELECT path, forwards, normalized_forwards, subscribers, views, reactions
        FROM {TABLE_NAME}
        WHERE normalized_forwards IS NOT NULL
        ORDER BY normalized_forwards DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"\nФото: {row[0]}")
        print(f"Пересылки: {row[1]} ({row[2]:.3f} на подписчика)")
        print(f"Подписчиков: {row[3]}")
        print(f"Просмотры: {row[4]}")
        print(f"Реакции: {row[5]}")
    
    conn.close()

if __name__ == "__main__":
    analyze_normalized() 