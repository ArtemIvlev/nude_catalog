import sqlite3
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_publication_date():
    """Добавляет поле с датой публикации в базу данных"""
    try:
        # Подключаемся к базе
        logger.info("Подключение к базе данных...")
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        
        # Добавляем новое поле
        logger.info("Добавление поля publication_date...")
        cur.execute("""
            ALTER TABLE photos_ok 
            ADD COLUMN publication_date TEXT
        """)
        
        # Устанавливаем текущую дату для всех опубликованных фотографий
        current_date = datetime.now().strftime('%Y-%m-%d')
        cur.execute("""
            UPDATE photos_ok 
            SET publication_date = ?
            WHERE status = 'published'
        """, (current_date,))
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
        logger.info("Поле publication_date успешно добавлено")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("Поле publication_date уже существует")
        else:
            raise
    except Exception as e:
        logger.error(f"Ошибка при добавлении поля: {e}")
        raise

if __name__ == "__main__":
    add_publication_date() 