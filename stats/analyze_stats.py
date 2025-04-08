import sqlite3
import sys
import os


from config import *

def analyze_stats():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Общая статистика
    cur.execute(f"""
        SELECT 
            COUNT(*) as total,
            COUNT(views) as with_views,
            COUNT(forwards) as with_forwards,
            COUNT(reactions) as with_reactions,
            AVG(views) as avg_views,
            AVG(forwards) as avg_forwards,
            MAX(views) as max_views,
            MAX(forwards) as max_forwards
        FROM {TABLE_NAME}
    """)
    stats = cur.fetchone()
    
    print("=== Общая статистика ===")
    print(f"Всего фотографий: {stats[0]}")
    print(f"С просмотрами: {stats[1]}")
    print(f"С пересылками: {stats[2]}")
    print(f"С реакциями: {stats[3]}")
    print(f"\nСреднее количество просмотров: {stats[4]:.1f}")
    print(f"Среднее количество пересылок: {stats[5]:.1f}")
    print(f"Максимум просмотров: {stats[6]}")
    print(f"Максимум пересылок: {stats[7]}")
    
    # Топ-10 по просмотрам
    print("\n=== Топ-10 по просмотрам ===")
    cur.execute(f"""
        SELECT path, views, forwards, reactions
        FROM {TABLE_NAME}
        WHERE views IS NOT NULL
        ORDER BY views DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"\nФото: {row[0]}")
        print(f"Просмотры: {row[1]}")
        print(f"Пересылки: {row[2]}")
        print(f"Реакции: {row[3]}")
    
    # Топ-10 по пересылкам
    print("\n=== Топ-10 по пересылкам ===")
    cur.execute(f"""
        SELECT path, views, forwards, reactions
        FROM {TABLE_NAME}
        WHERE forwards IS NOT NULL
        ORDER BY forwards DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"\nФото: {row[0]}")
        print(f"Просмотры: {row[1]}")
        print(f"Пересылки: {row[2]}")
        print(f"Реакции: {row[3]}")
    
    # Анализ реакций
    print("\n=== Анализ реакций ===")
    cur.execute(f"""
        SELECT reactions
        FROM {TABLE_NAME}
        WHERE reactions IS NOT NULL
    """)
    reactions = cur.fetchall()
    
    reaction_counts = {}
    for row in reactions:
        if row[0]:
            for reaction in row[0].split(','):
                try:
                    emoji, count = reaction.split(':')
                    reaction_counts[emoji] = reaction_counts.get(emoji, 0) + int(count)
                except:
                    continue
    
    print("\nРаспределение реакций:")
    for emoji, count in sorted(reaction_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{emoji}: {count}")
    
    conn.close()

if __name__ == "__main__":
    analyze_stats() 