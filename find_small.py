import os
from PIL import Image
import sqlite3

# Параметры подключения
DB_PATH = 'database.db'  # Путь к вашей базе данных
IMAGE_DIR = r"/mnt/smb/OneDrive/Pictures/!Фотосессии/"         # Папка с изображениями

# Имя таблицы
TABLE_NAME = "photos_ok"



# Функция для получения списка столбцов таблицы
def get_table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [column[1] for column in cursor.fetchall()]
    return columns

# Функция для получения размеров изображения
def get_image_size(image_path):
    try:
        with Image.open(image_path) as img:
            return img.size  # Возвращает кортеж (width, height)
    except Exception as e:
        print(f"Ошибка при обработке изображения {image_path}: {e}")
        return None

# Подключение к базе данных
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Получение списка столбцов в таблице
columns = get_table_columns(cursor, TABLE_NAME)

# Проверка наличия столбца 'is_small', если нет - добавление
if 'is_small' not in columns:
    cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN is_small INTEGER DEFAULT 0;")
    conn.commit()
    print(f"Столбец 'is_small' успешно добавлен в таблицу '{TABLE_NAME}'.")

# Получение списка всех изображений из базы данных
cursor.execute(f"SELECT id, path FROM {TABLE_NAME}")
rows = cursor.fetchall()

# Обработка каждого изображения
for row in rows:
    image_id, image_path = row
    full_image_path = os.path.join(IMAGE_DIR, image_path)

    # Получение размеров изображения
    size = get_image_size(full_image_path)
    if size:
        width, height = size
        is_small = 1 if width < 2500 and height < 2500 else 0

        # Обновление записи в базе данных
        cursor.execute(
            f"UPDATE {TABLE_NAME} SET is_small = ? WHERE id = ?",
            (is_small, image_id)
        )
        conn.commit()
        print(f"Обновлена запись для изображения {image_id}: is_small = {is_small}")

# Закрытие соединения с базой данных
conn.close()
